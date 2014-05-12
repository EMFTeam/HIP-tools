#!/usr/bin/perl

use strict;
use warnings;
use Carp;
use Readonly;
use Getopt::Long qw(:config gnu_getopt);
use Cwd qw(abs_path);
use File::Spec;
use File::Path qw(make_path remove_tree);

## Configuration variables ##

my $base_dir = "/cygdrive/c/Users/Stark/Documents/GitHub";
my $vanilla_dir = "/cygdrive/c/Program Files (x86)/Steam/SteamApps/common/Crusader Kings II"; # must be absolute

my @components = (
	{ name => 'Vanilla', dirs => [ $vanilla_dir ], vanilla => 1 }, # comes first
#	{ name => 'HIP', dirs => ['HIP_Common/HIP_Common'] },
	{ name => 'PB', dirs => ['PB/ProjectBalance', 'PB/PB + SWMH'] },
	{ name => 'SWMH', dirs => ['SWMH/SWMH', 'SWMHLogic/SWMH_Logic'] },
	{
		name => 'VIET',
		dirs => [
			'VIET/VIET_Immersion/common',
			'VIET/VIET_Immersion/vanilla',
			'VIET/VIET_Immersion/PB',
			'VIET/VIET_Events',
			'VIET/PB_VIET_Events',
			'VIET/VIET_Assets',
		],
	},
);

my $opt_block_sz = 10_000;
my $opt_output_dir = File::Spec->catdir(abs_path(), 'charalloc');
my $opt_force = 0;

## End of configuration variables ##

GetOptions(
	'b|block-size=i' => \$opt_block_sz,
    'o|output-dir=s' => \$opt_output_dir,
	'f|force' => \$opt_force) or croak;

croak "Block size must be a positive integer multiple of 10 (-b, --block-size)"
	unless ($opt_block_sz > 0 && $opt_block_sz % 10 == 0);
	
if (-e $opt_output_dir) {
	if ($opt_force) {
		remove_tree($opt_output_dir);
	}
	else {
		croak "Output directory preexists (use -f, --force)";
	}
}

make_path($opt_output_dir) or croak "Couldn't create output path: $opt_output_dir";

# We'll be changing dirs, so we need the output path absolute.
$opt_output_dir = abs_path($opt_output_dir);

# Switch current working directory to the HIP components' base directory
chdir $base_dir or croak "Couldn't change working directory: $!: $base_dir";

# Master map of character IDs defined in history files to their source(s)
my %char = ();

Readonly my $ID_MIN => -1;
Readonly my $ID_MAX => (1<<30)-1;
Readonly my $CHAR_HIST_DIR => 'history/characters';

my $n_char_scanned = 0;
my $component_id = 0;

for my $c (@components) {
#	print "$c->{name}\n";

	# Initialize component-level accounting
	$c->{n} = 0;
	$c->{n_xd} = 0;
	$c->{n_uniq} = 0;

	$c->{max} = $ID_MIN; # Maximum character ID defined
	$c->{min} = $ID_MAX; # Minimum character ID defined
	$c->{max_nv} = $ID_MIN; # Maximum non-vanilla character ID defined
	$c->{min_nv} = $ID_MAX; # Minimum non-vanilla character ID defined
	
	$c->{mask} = 1;
	$c->{mask} <<= $component_id;
	$c->{id} = $component_id++;

	# Scan all components' history files for characters (vanilla first)
	
	for my $mod_dir (@{ $c->{dirs} }) {
		my $hist_dir = File::Spec->catdir($mod_dir, $CHAR_HIST_DIR);

		next unless -e $hist_dir; # Only interested in those components feat. characters
	
#		print "  $hist_dir\n";

		for my $filename ( load_txt_filenames($hist_dir) ) {
			$n_char_scanned += my $n_char = parse_char_file( File::Spec->catfile($hist_dir, $filename), $c, \%char );
#			print "    $filename ($n_char)\n";
		}
	}
}

print "\nTotal character definitions scanned: $n_char_scanned\n";


# Calculate collisons and other stuff which doesn't really matter
for my $ch (values %char) {
	my @defs = @{ $ch->{definitions} };
	
	if (scalar @defs > 1 && !$ch->{vanilla}) {
		# Non-vanilla character has multiple definitions within HIP
		
		for my $def (@defs) { ++$def->{component}{n_xd} }
	}
	elsif (scalar @defs == 1) {
		# Character is truly unique within all of HIP
		
		for my $def (@defs) { ++$def->{component}{n_uniq} }
	}
	else {
		# Collision, but with a vanilla character, so it's not of interest.
	}
}


# And here's where we can do a lot with overlapping character ID allocation blocks but
# presently do no analysis whatsoever...


# Sorted by unique character definitions, descending
for my $c ( sort { $b->{n_uniq} <=> $a->{n_uniq} } @components ) {

	print "\n=="."\U$c->{name}"."==\n";
	print "Truly unique characters:       $c->{n_uniq}\n";
	
	unless (exists $c->{vanilla}) {
		print "Collisions (vanilla excluded): $c->{n_xd}\n";
		print "Minimum non-vanilla ID:        $c->{min_nv}\n";
		print "Maximum non-vanilla ID:        $c->{max_nv}\n";
	}
	else {
		print "Minimum ID:                    $c->{min}\n";
		print "Maximum ID:                    $c->{max}\n";	
	}
}

exit 0;


sub load_txt_filenames {
	my $dir = shift;
	opendir(my $d, $dir) or croak "opendir: $!: $dir";
	return sort grep { /\.txt$/ } readdir $d;
}


sub parse_char_file {
	my $file = shift;
	my $c = shift;
	my $chars = shift;
		
	open(my $f, '<', $file) or croak "failed to open character file: $!: $file";
	my $n_line = 0;
	my $n_char = 0;
	
	while (<$f>) {
		++$n_line;
		
		next if /^\s*\#/;
		next unless /\{/;
		
		# at top-level & current line contains at least one opening brace
		
		my $id;
		
		if (/^\s*(\d+)\s*=\s*\{\s*(?:\#[^\r]*)?\r?$/) {
			# well-formed char definition opening line
			$id = 0+$1;
		}
		else {
			parse_err($file, $n_line, "failed to recognize character opening statement (span multiple lines?)");
		}

		my $def = { id => $id, component => $c, file => $file, line => $n_line };
		
		# we're now at brace nest level 1, directly inside a char definition.
		# only return here once the file pointer is advanced to the line or EOF
		# following its final closing brace.
		
		$n_line = consume_char($f, $file, $n_line, $id);
		++$n_char;
		
		my $vanilla = (exists $c->{vanilla});
		my $char;
		
		if (exists $chars->{$id}) {
			# character already defined by component(s).
			$char = $chars->{$id};
			
			# append to definitions list and update the mask for collisions.
			$char->{mask} |= $c->{mask};
			push @{ $char->{definitions} }, $def;
		}
		else {
			# a freshie.
			$char = $chars->{$id} = {
				definitions => [ $def ],
				mask => $c->{mask},
				vanilla => $vanilla,
			};
		}
		
		++$c->{n};
		$c->{max} = $id if $id > $c->{max};
		$c->{min} = $id if $id < $c->{min};
		
		unless ($char->{vanilla}) {
			$c->{max_nv} = $id if $id > $c->{max_nv};
			$c->{min_nv} = $id if $id < $c->{min_nv};
		}
	}
	
	return $n_char;
}


sub consume_char {
	my $f = shift;
	my $file = shift;
	my $n_line = shift;
	my $id = shift;
	
	my $start_line = $n_line;
	my $nest = 1;
	
	while (<$f>) {
		++$n_line;
		
		next if /^\s*\#/;
		
		# could definitely be a lot more terse with validation here, but whatever.
		# (  } ... { counts the same as { ... } if on the same line  )
		
		while (/([}{#])/g) {
			last if $1 eq '#';
		
			$nest += ($1 eq '{');
			$nest -= ($1 eq '}');
			
			parse_err($file, $n_line, "too many closing braces for character $id: starts at line $start_line")
				if $nest < 0;
		}
		
		last unless $nest > 0;
	}
	
	parse_err($file, $n_line, "unexpected EOF in character $id: starts at line $start_line")
		if $nest > 0;
	
	return $n_line;
}


sub parse_err {
	my $file = shift;
	my $line = shift;
	err("parse error: ", @_, ": file '$file': line $line");
}


sub err {
	print STDERR "fatal: ", @_, "\n";
	exit 1;
}
