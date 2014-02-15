#!/usr/bin/perl

use strict;
use warnings;

use Carp;
use Getopt::Long qw(:config gnu_getopt);
use Readonly;

use Data::Dumper;

#Readonly my $TRAIT_DIR => '/cygdrive/c/Users/Stark/Documents/Paradox Interactive/Crusader Kings II/mod/Historical Immersion Project/common/traits';
Readonly my $TRAIT_DIR => '/cygdrive/c/Users/Stark/Documents/GitHub/PB/ProjectBalance/common/traits';

my $opt_vrb = 0;
my $opt_codegen;
my $opt_showflags = 0;
my $opt_trait_dir = $TRAIT_DIR;

GetOptions('v|verbose+' => \$opt_vrb,
	   'codegen=s' => \$opt_codegen,
	   'show-flags' => \$opt_showflags,
	   'd|dir=s' => \$opt_trait_dir,
    );

chdir $opt_trait_dir or croak "chdir: $!: $opt_trait_dir";

opendir my $dh, '.' or croak "opendir: $!";
my @files = sort {$a cmp $b } grep { /\.txt$/i } readdir $dh;
closedir $dh;

my %flag_count = (); # stats only
my %traits = ();
my $max_id = 0;

for my $f (@files) {
    open my $fh, '<', $f or croak "open: $!: $f";

    my $n_line = 0;
    my $n_traits = 0;

    while (<$fh>) {
	++$n_line;

	if (/^\s*([0-9a-z_]+)\s*=\s*[{]/o) {
	    my $name = $1;
	    croak "trait $name redefined: $f:$n_line" if exists $traits{$name};

	    my $t = { _name => $name, _file => $f, _line => $n_line, _id => ++$max_id };
	    $traits{$name} = $t;

	    my $in_block = 0;

	    while (my $line = <$fh>) {
		++$n_line;

		if (!$in_block) {
		    if ($line =~ /^\s*([a-z_]+)\s*=\s*(yes|no)/o) {
			$t->{$1} = ($2 eq 'yes')?1:0;
			++$flag_count{$1};
		    }
		    elsif ($line =~ /^\s*([a-z_]+)\s*=\s*([a-zA-Z0-9_\.\-]+)/o) {
			$t->{$1} = $2;
		    }
		    elsif ($line =~ /^\s*potential\s*=\s*[{]/op) {
			$t->{has_potential} = 1;
			$in_block = 1 if ${^POSTMATCH} !~ '}';
		    }
		    elsif ($line =~ /^\s*command_modifier\s*=\s*[{]/op) {
			$t->{has_command_modifier} = 1;
			$in_block = 1 if ${^POSTMATCH} !~ '}';
		    }
		    elsif ($line =~ /^\s*opposites\s*=\s*[{]/op) {
			$t->{opposites} = read_opposites($f, \$n_line, $fh, ${^POSTMATCH});
		    }
		    elsif ($line =~ /^\s*[}]/o) {
			last;
		    }
		}
		elsif ($line =~ /^\s*[}]/o) {
		    $in_block = 0;
		}
	    }

	    ++$n_traits;
	}
    }

    print STDERR "$f: traits ".($max_id-$n_traits+1)."-$max_id ($n_traits total)\n" if $opt_vrb > 1;
}

print STDERR "total traits parsed (".(scalar @files)." files): $max_id\n" if $opt_vrb;

if ($opt_showflags) {

    for my $f (sort { $flag_count{$b} <=> $flag_count{$a} } keys %flag_count) {
	print "$f ($flag_count{$f})\n";
    }
}

my @trait_list = sort { $a->{_id} <=> $b->{_id} } values %traits;
print STDERR Data::Dumper->Dump( \@trait_list, [map { $_->{_name} } @trait_list] ) if $opt_vrb > 2;

my @ed_traits = sort { $a->{_id} <=> $b->{_id} } grep { $_->{education} } values %traits;
my @leader_traits = sort { $a->{_id} <=> $b->{_id} } grep { $_->{leader} } values %traits;
my @persona_traits = sort { $a->{_id} <=> $b->{_id} } grep { $_->{personality} } values %traits;
my @birth_traits = sort { $a->{_id} <=> $b->{_id} } grep { $_->{birth} } values %traits;

my %genes = make_genotypes(@birth_traits);

print "# % pb_rr.pl --codegen=$opt_codegen\n" if $opt_codegen;

if ($opt_codegen) {
    if ($opt_codegen =~ /^ed_select_([0-3])$/) {
	my $tier = 0+$1;

	my @weights = (
	    [15,30,30,25],
	    [10,25,30,35],
	    [ 5,20,30,45],
	    [ 0,15,30,55]
	    );

	my $tier_dist = $weights[$tier];

	my @ed_traits = sort { $a->{_id} <=> $b->{_id} } grep { exists $_->{education} } values %traits;

	print "random_list = {\n";

	for my $i (0..$#ed_traits) {
	    my $weight = $tier_dist->[$i%4];
	    $weight /= 5; # all the base weights are multiples of 5 (they represent percentages)
	    $weight *= 4 unless $ed_traits[$i]->{priest}; # priest traits 1/4 as likely as others
	    print "\t$weight = { add_trait = $ed_traits[$i]->{_name} }\n" if $weight;
	}

	print "}\n";

    }
    elsif ($opt_codegen eq 'rm_leaders') {
	for my $t (@leader_traits) {
	    print "remove_trait = $t->{_name}\n";
	}
    }
    elsif ($opt_codegen eq 'leader_select') {
	print "random_list = {\n";

	for my $t (@leader_traits) {
	    print "\t10 = { add_trait = $t->{_name} }\n" if (!exists $t->{random} || $t->{random});
	}

	print "}\n";
    }
    elsif ($opt_codegen eq 'rm_persona') {
	for my $t (@persona_traits) {
	    print "remove_trait = $t->{_name}\n";
	}
    }
    elsif ($opt_codegen =~ /^persona_select$/) {

	my @ages = (
	    [ 6, 8],
	    [ 8,10],
	    [10,12],
	    [12,14],
	    [14],
	    );

	for my $n_traits (1..5) {

	    my ($age_begin, $age_end) = @{ $ages[$n_traits-1] };

	    print "if = {\n";
	    print "\t" x 1, "limit = {\n";
	    print "\t" x 2, "age = $age_begin\n";
	    print "\t" x 2, "NOT = { age = $age_end }\n" if $age_end;
	    print "\t" x 1, "}\n";
	    print "\n";

	    for my $n (1..$n_traits) {

		print "\t" x 1, "# Roll a new personality trait: ROUND $n OF $n_traits\n";
		print "\t" x 1, "random_list = {\n";

		for my $t (@persona_traits) {

		    next if (exists $t->{random} && !$t->{random});

		    print "\t" x 2, "10 = {\n";

		    my @not_when;

		    if ($t->{has_potential}) {
			croak "unhandled potential clause in personality trait $t->{_name}"
			    unless $t->{_name} eq 'chaste';

			push @not_when, "religion_group = muslim"; # chaste
		    }


		    if (exists $t->{opposites}) {
			
			for my $opposite (@{ $t->{opposites} }) {
			    
			    croak "personality trait $t->{_name} references undefined opposite trait '$opposite'"
				unless exists $traits{$opposite};

			    push @not_when, "trait = $opposite";
			}
		    }

		    if (@not_when) {
			print "\t" x 3, "if = {\n";

			if (scalar @not_when > 1) {
			    print "\t" x 4, "limit = {\n";
			    print "\t" x 5, "NOT = {\n";

			    for my $condition (@not_when) {
				print "\t" x 6, "$condition\n";
			    }
			    
			    print "\t" x 5, "}\n"; # END: NOT
			    print "\t" x 4, "}\n"; # END: limit
			}
			else {
			    print "\t" x 4, "limit = { NOT = { $not_when[0] } }\n"
			}


			print "\t" x 4, "add_trait = $t->{_name}\n";
			print "\t" x 3, "}\n"; # END: if
		    }
		    else {
			print "\t" x 3, "add_trait = $t->{_name}\n";
		    }
		    
		    print "\t" x 2, "}\n";
		}

		print "\t" x 1, "}\n";
	    }

	    print "}\n";
	}
    }
    elsif ($opt_codegen eq 'rm_genes') {

	for my $t (@birth_traits) {
	    print "remove_trait = $t->{_name}\n";
	}
    }
    elsif ($opt_codegen =~ /gene_select:chance_mult=([\.\d]+)$/) {
	my $chance_mult = 0+$1;

	for my $gene (sort keys %genes) {
	    
	    my $g = $genes{$gene};

	    print "\n# Genotype: $gene\n";
	    print "random_list = {\n";

	    my $none_wt = 10000;
	    
	    for my $t (@{ $g->{traits} }) {
		my $wt = 0 + sprintf("%d", $t->{birth} * $chance_mult);

		print "\t$wt = { add_trait = $t->{_name} }\n";
		$none_wt -= $wt;
	    }

	    print "\t$none_wt = { }\n";

	    print "}\n";
	}
    }
    elsif ($opt_codegen =~ /^gene_inherit:chance_offset=(-?\d+)$/) {
	my $chance_offset = 0+$1;

	for my $parent ( qw(mother father) ) {

	    print "\n# Inherit ${parent}'s traits...\n";
	    print $parent." = {\n";

	    for my $t (sort { $a->{gene} cmp $b->{gene} } @birth_traits) {

		next unless (exists $t->{inherit_chance} && $t->{inherit_chance});

		my $new_chance = $t->{inherit_chance} + $chance_offset;
		$new_chance = 100 if $new_chance > 100;

		if ($new_chance <= 0) {
		    print "\t" x 1, "# Skipped $t->{_name} due to negative chance_offset rendering it uninheritable\n";
		    next;
		}

		my $g = $genes{ $t->{gene} };

		print "\t" x 1, "if = { #$t->{gene}\n";
		print "\t" x 2, "limit = { trait = $t->{_name} }\n";
		print "\t" x 2, "random = {\n";
		print "\t" x 3, "chance = $new_chance\n";

		unless (scalar @{$g->{traits}} > 1) {
		    print "\t" x 3, "ROOT = { add_trait = $t->{_name} }\n";
		}
		else {
		    print "\t" x 3, "ROOT = {\n";

		    for my $u (@{ $g->{traits} }) {
			next if $u->{_id} == $t->{_id};
			print "\t" x 4, "remove_trait = $u->{_name}\n";
		    }

		    print "\t" x 4, "add_trait = $t->{_name}\n";
		    print "\t" x 3, "}\n"; # END: ROOT
		}

		print "\t" x 2, "}\n"; #END: random
		print "\t" x 1, "}\n"; #END: if
	    }

	    print "}\n"; #END: parent's scope
	}
    }
    else {
	print STDERR "unrecognized codegen key '$opt_codegen'\n";
    }
}

# NOTE: opposites clause references are still unresolved / unchecked

exit 0;


# Build genotypes from opposite birth trait groupings, assume
# opposites are always mutual (they always are for birth traits,
# or it's an error).
sub make_genotypes {
    my @birth_traits = @_;

    my %genes = ();

    for my $t (@birth_traits) {

	my @group = $t;
	push(@group, map { $traits{$_} } @{ $t->{opposites} } )
	    if exists $t->{opposites};

	# Canonicalize genotype ID
	my $gene = join('', 
			map {
			    my @p = split('_', $_->{_name});
			    my $word = '';
			    
			    for my $p (@p) {
				$word .= "\u$p";
			    }
			    
			    $word;
			}
			sort { $a->{_name} cmp $b->{_name} }
			@group
	    );

	next if exists $genes{$gene}; # Assume that a past clustering always
	                              # produces an equivalent result.

	my $g = { traits => \@group };
	$genes{$gene} = $g;

	for my $u (@group) {
	    $u->{gene} = $gene;
	}
    }

    return %genes;
}



sub read_opposites {
    my $f = shift;
    my $rn_line = shift;
    my $fh = shift;
    my $start = shift;

    my @opposites = ();

    my $buf = $start;

    if ($buf =~ '}') {
	$buf =~ s/[}].*$//;
    }
    else {
	# multi-line case

	while (my $line = <$fh>) {
	    ++$$rn_line;

	    if ($line =~ /^(.*)[}]/) {
		$buf .= $1;
		last;
	    }
	    else {
		$buf .= $line;
	    }
	}
    }

    # trim any leading/trailing whitespace or CRLF chars from multi-line buf
    $buf =~ s/^[\s\r\n]+//s;
    $buf =~ s/[\s\r\n]+$//s;

    # split buf into tokens on whitespace or CRLF runs
    @opposites = split(/[\s\r\n]+/s, $buf);

    croak "$f:$$rn_line: parse failed: empty opposites clause: buf='$buf'"
	unless @opposites;

    return \@opposites;
}

