#!/usr/bin/perl

use strict;
use warnings;

use Carp;
use Getopt::Long qw(:config gnu_getopt);
use Readonly;

use Time::HiRes;

use SaveFile;

Readonly my $ARCHIVE_BASE_DIR => '/cygdrive/c/Users/Stark/Documents/asrotor';

croak "archive base directory not found: $ARCHIVE_BASE_DIR" unless (-d $ARCHIVE_BASE_DIR);

my $opt_name;
my $opt_start = 0;
my $opt_end = 1000;

GetOptions(
    'n|name=s' => \$opt_name,
	's|start=d' => \$opt_start,
	'e|end=d' => \$opt_end)
    or croak;

croak "you must specify a name for the savegame series with --name" unless $opt_name;

my $sgs_dir = "$ARCHIVE_BASE_DIR/$opt_name";
my $time_start = time();

croak "savegame series directory not found: $sgs_dir" unless (-d $sgs_dir);

opendir(my $dh, $sgs_dir) or croak $!;

my @sg_filenames = ();

while (readdir $dh) {
	if (/\.(\d+)\.ck2$/) {
		$sg_filenames[ $1 - 1 ] = "$sgs_dir/$_";
	}
}

closedir $dh;

# @sg_files = ( $sg_files[0] );

my $stats = {};
my $prev_sf;

for my $i (0..$#sg_filenames) {
	next if ($i < $opt_start-1);
	last if ($opt_end-1 < $i);

	my $sf;
	
	if (!defined $sg_filenames[$i]) {
		print "series broken: missing save #$i\n";
	}
	else {
		$sf = SaveFile->new($sg_filenames[$i]);

		my $tstart = Time::HiRes::time();
		$sf->parse();
		my $tend = Time::HiRes::time();
		
		my $n_chars = scalar keys %{ $sf->chars() };
		print "parsed: save #$i: $sf->{filename} (".sprintf("%.1f", $tend-$tstart)."s): $n_chars characters\n";
	}
	
	analyze($prev_sf, $sf, $stats);
	$prev_sf = $sf;
}

exit 0;

#####

sub analyze {
	my ($psf, $sf, $stats) = @_;
	
	if (!defined $sf) {
		# hole in the series, currently not handled.
		croak "analyzer doesn't currently support series with holes in them";
	}
	
	if (!exists $stats{start_date}) {
		# first in the series.
		# $psf is undefined too.
		
		$stats{start_date} = $sf->start_date;
	}
	
	for my $char (values %{ $sf->chars }) {
	}
}

