#!/usr/bin/perl

use strict;
use warnings;

use Carp;
use Getopt::Long qw(:config gnu_getopt);
use File::stat;
use File::Copy;
use Readonly;


Readonly my $LIVE_DIR => '/cygdrive/c/Users/Stark/Documents/Paradox Interactive/Crusader Kings II/HIP_ztrulers/save games';
Readonly my $ARCHIVE_BASE_DIR => '/cygdrive/c/Users/Stark/Documents/asrotor';

croak "autosave monitoring directory not found: $LIVE_DIR" unless (-d $LIVE_DIR);
croak "archive base directory not found: $ARCHIVE_BASE_DIR" unless (-d $ARCHIVE_BASE_DIR);

my $opt_name;
my $opt_continue = 0;

GetOptions(
    'n|name=s' => \$opt_name,
    'c|continue' => \$opt_continue)
    or croak;

croak "you must specify a name for the savegame series with --name" unless $opt_name;

my $autosave_file = "$LIVE_DIR/autosave.ck2";
my $archive_dir = "$ARCHIVE_BASE_DIR/$opt_name";
my $counter_file = "$archive_dir/.counter";

my $time_start = time();
my $time_last = $time_start;
my $counter_start = 0;
my $counter = 0;

sub finish {
	print "Archived ".($counter-$counter_start)." autosaves, series totaling $counter, over ".sprintf("%.2f", (time()-$time_start)/60)." minutes.\n";
	print "Path: $archive_dir\n";
	exit 0;
}

$SIG{INT} = \&finish;


if (-e $archive_dir) {
    croak "archive directory already exists; continue existing archive with --continue" unless $opt_continue;
    croak "cannot continue without series counter file" if (! -f $counter_file);

    read_counter_file();
	$counter_start = $counter;
}
else {
    mkdir($archive_dir) or croak $!;
    update_counter_file();
}

my $as_mtime = (-f $autosave_file) ? stat($autosave_file)->mtime : 0;

while (1) {
	
	my $st = stat($autosave_file);
	
	if (defined $st && $st->mtime > $as_mtime) {
		# autosave file is present and its mtime is newer than previously recorded
		
		$as_mtime = $st->mtime;
		
		# sleep an extra 15 seconds to allow for the game to do a slow write-out
		# of a very large save.  we may otherwise catch the file in the middle of
		# being written.
		
		sleep(15);
		
		# now move the save to the head of our archive series

		++$counter;
		update_counter_file();
		
		my $dest_file = "$opt_name.$counter.ck2";
		File::Copy::move($autosave_file, "$archive_dir/$dest_file") or croak $!;
		
		my $now = time();
		print STDERR "archived: $dest_file (".($now-$time_last)."s)\n";
		$time_last = $now;
	}
	
	sleep(1);
}

# currently not reachable, as a SIGINT is required to stop monitoring the save directory
finish();



sub update_counter_file {
    open(my $cf, '>', $counter_file) or croak $!;
    $cf->print("$counter\n");
}

sub read_counter_file {
    open(my $cf, '<', $counter_file) or croak $!;
    $counter = <$cf>;
    $counter =~ s/\r?\n$//;
}
