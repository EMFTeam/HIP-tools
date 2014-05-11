#!/usr/bin/perl

use strict;
use warnings;
use Carp;
use Getopt::Long qw(:config gnu_getopt);
use File::Spec;
use Data::Dumper;
use File::Basename qw(basename);

my $CHAR_HIST_DIR = 'history/characters';

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

## End of config. variables ##


# Switch current working directory to the HIP components' base directory
chdir $base_dir or croak "could not change working directory: $!: $base_dir";

# Master map of character IDs defined in history files to their source(s)
my %char = ();
my $n_char_scanned = 0;

my $ID_MIN = -1;
my $ID_MAX = (1<<30)-1;

# Scan all components' history files for characters (vanilla first)
for my $c (@components) {
	print "$c->{name}\n";

	# Initialize component-level counters
	$c->{n} = 0; # Num. of characters defined
	$c->{n_xd} = 0; # Num. of characters that collide with itself or other components, aside from vanilla
	$c->{max} = $ID_MIN; # Maximum character ID defined
	$c->{min} = $ID_MAX; # Minimum character ID defined
	$c->{max_nv} = $ID_MIN; # Maximum non-vanilla character ID defined
	$c->{min_nv} = $ID_MAX; # Minimum non-vanilla character ID defined
	
	for my $mod_dir (@{ $c->{dirs} }) {
		my $hist_dir = File::Spec->catdir($mod_dir, $CHAR_HIST_DIR);

		next unless -e $hist_dir; # Only interested in those components feat. characters
	
		print "  $hist_dir\n";

		for my $filename ( load_txt_filenames($hist_dir) ) {
			$n_char_scanned += my $n_char = parse_char_file( File::Spec->catfile($hist_dir, $filename), $c, \%char );
			print "    $filename ($n_char)\n";
		}
	}
}

print "\nTotal character definitions scanned: $n_char_scanned\n";

# Calculate collisons
for my $ch (values %char) {
	next if $ch->{vanilla};
	
	if (scalar @{ $ch->{definitions} } > 1) {
		for my $def (@{ $ch->{definitions} }) {
			++$def->{component}{n_xd};
			
			# And here's where we can do a lot with multiply-defined characters w/i HIP
			# and their exact locations but presently only count them...
		}
	}
}

# And here's where we can do a lot with overlapping character ID allocation blocks but
# presently do no analysis whatsoever...

# Calculate "unique" definitions (somewhat strange, because it includes vanilla characters,
# and it is a measure of those actually defined or overridden by the mod-- not how many the
# mod, in combination with vanilla files not overridden, might actually present in-game). A
# lower number generally indicates less complexity and probably cleaner merge state with
# vanilla.  OTOH, the component may just feature a lot of new characters.
map { $_->{n_uniq} = $_->{n} - $_->{n_xd} } @components;

# Sorted by unique character definitions, descending
for my $c ( sort { $b->{n_uniq} <=> $a->{n_uniq} } @components ) {

	print "\n\U$c->{name}\n";
	print "Unique characters overridden (vanilla included): $c->{n_uniq}\n";
	print "Collisions: $c->{n_xd}\n";
	
	unless (exists $c->{vanilla}) {
		print "Minimum non-vanilla ID: $c->{min_nv}\n";
		print "Maximum non-vanilla ID: $c->{max_nv}\n";
	}
	else {
		print "Minimum ID: $c->{min}\n";
		print "Maximum ID: $c->{max}\n";	
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
			# append to definitions list.
			
			#++$c->{n_xd} unless $char->{vanilla}; # only count as collision if non-vanilla
			push @{ $char->{definitions} }, $def;
		}
		else {
			# a freshie.
			$char = $chars->{$id} = { vanilla => $vanilla, definitions => [ $def ] };
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
