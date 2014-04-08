#!/usr/bin/perl

use strict;
use warnings;

use Carp;
use Getopt::Long qw(:config gnu_getopt);
use File::stat;
use File::Copy;
use File::Basename;
use File::Spec;
use POSIX qw(setsid);
use Readonly;

my $PROG = basename($0);

my $prog_no_ext = $PROG;
$prog_no_ext =~ s/^\.//;
$prog_no_ext =~ s/^(.*?)\..*$/$1/;

my $home_doc_dir = File::Spec->catdir(qw( /cygdrive c Users ), $ENV{USER}, 'Documents');

my $ARCHIVE_DIR_DEFAULT = File::Spec->catdir($home_doc_dir, $prog_no_ext);
$ARCHIVE_DIR_DEFAULT = undef unless -d $ARCHIVE_DIR_DEFAULT;

my $USER_DIR_DEFAULT = File::Spec->catdir($home_doc_dir, 'Paradox Interactive', 'Crusader Kings II');
$USER_DIR_DEFAULT = undef unless -d $USER_DIR_DEFAULT;


my $opt_archive_dir = $ARCHIVE_DIR_DEFAULT;
my $opt_user_dir = $USER_DIR_DEFAULT;
my $opt_mod_user_dir;
my $opt_name;
my $opt_continue = 0;
my $opt_bench_file = 0;
my $opt_daemon = 0;

GetOptions(
	'a|archive-dir=s' => \$opt_archive_dir,
	'u|user-dir=s' => \$opt_user_dir,
	'm|mod-user-dir=s' => \$opt_mod_user_dir,
    'n|name=s' => \$opt_name,
    'c|continue' => \$opt_continue,
	'D|daemonize' => \$opt_daemon,
	) or croak;

croak "specify a user directory with --user-dir" unless $opt_user_dir;
croak "specify a name for the savegame series with --name" unless $opt_name;
croak "specify an archive root directory with --archive-dir" unless $opt_archive_dir;

croak "user directory not found: $opt_user_dir" unless -d $opt_user_dir;
croak "archive base directory not found: $opt_archive_dir" unless -d $opt_archive_dir;

my $user_dir = $opt_user_dir;

if ($opt_mod_user_dir) {
	$user_dir = File::Spec->catdir($opt_user_dir, $opt_mod_user_dir);
	
	unless (-e $user_dir) {
		mkdir $user_dir or croak "folder creation failed: $!: $user_dir";
	}
}

my $save_dir = File::Spec->catfile($user_dir, 'save games');
my $autosave_file = File::Spec->catfile($save_dir, 'autosave.ck2');
my $archive_dir = File::Spec->catfile($opt_archive_dir, $opt_name);
my $counter_file = File::Spec->catfile($archive_dir, '.counter');
my $bench_file = File::Spec->catfile($archive_dir, 'benchmark_'.$opt_name.'.csv');
my $pid_file = File::Spec->catfile($archive_dir, '.pid');

unless (-e $save_dir) {
	mkdir $save_dir or croak "folder creation failed: $!: $save_dir";
}

if (-e $pid_file) {
	open(my $pf, '<', $pid_file);
	my $pid = <$pf>;
	$pf->close;

	if (kill 0 => $pid) {
		print STDERR "A daemon instance is already running on this series: pid $pid\n";
	}
	else {
		unlink($pid_file);
	}
}

my $bf;
my $time_start = time();
my $time_last = $time_start;
my $counter_start = 0;
my $counter = 0;

sub finish {
	$bf->close;

	unlink $pid_file if $opt_daemon;
	
	print "Archived ".($counter-$counter_start)." autosaves, series totaling $counter, over ".sprintf("%.2f", (time()-$time_start)/60)." minutes.\n";
	print "Path: $archive_dir\n";
	exit 0;
}

$SIG{INT} = \&finish;
$SIG{TERM} = \&finish;


if (-e $archive_dir) {
    croak "archive directory already exists; continue existing archive with --continue" unless $opt_continue;
    croak "cannot continue without series counter file" if (! -f $counter_file);

    read_counter_file();
	$counter_start = $counter;
	open($bf, '>>', $bench_file) or croak "file open failed: $!: $bench_file";
}
else {
    mkdir($archive_dir) or croak $!;
    update_counter_file();
	open($bf, '>', $bench_file) or croak "file open failed: $!: $bench_file";
	$bf->print("Relative Year;Duration (seconds);File Size (MB)\n");
}

my $as_mtime = (-f $autosave_file) ? stat($autosave_file)->mtime : 0;
my $waiting = 1;

while (1) {

	if ($waiting) {
		print STDERR "Waiting for first autosave (start the game)...\n";
		$waiting = 0; # only print this reminder at the start
		
		daemonize() if $opt_daemon;
	}

	my $st = stat($autosave_file);
	
	if (defined $st && $st->mtime > $as_mtime) {
		# autosave file is present and its mtime is newer than previously recorded
		
		# sleep an extra 15 seconds to allow for the game to do a slow write-out
		# of a very large save.  we may otherwise catch the file in the middle of
		# being written.
		
		sleep(15);
		
		# redo the stat, in case the mtime is later now due to an in-progress write
		# (and, if benchmarking, we want the exact time between the end-of-write
		# of autosaves)
		$st = stat($autosave_file);
		my $size_mb = sprintf('%0.1f', $st->size / 1_000_000);
	
		if ($counter == $counter_start) { # the first save in a run can't be clocked
			$bf->print($counter, ';', ';', $size_mb, "\n");
		}
		else {
			$bf->print($counter, ';', $st->mtime-$as_mtime, ';', $size_mb, "\n");
		}
		
		$bf->flush;
		$as_mtime = $st->mtime; # rotate the previous mtime
		
		# and we now update the series index (for benchmark purposes, an interval of
		# a year is assumed, and the offsets start at 0; hence, only updating now)
		++$counter;
		update_counter_file();
		
		# now move the save to the head of our archive series
				
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

sub daemonize {
	print STDERR "Detaching to run in the background (kill with INT/TERM)...\n";
	
	my $null = File::Spec->devnull;
	
	chdir($archive_dir)       or croak "can't chdir: $!: $archive_dir";
	open(STDIN,  "<", $null)  or croak "can't read $null: $!";
	open(STDOUT, ">", $null)  or croak "can't write to $null: $!";
	defined(my $pid = fork()) or croak "can't fork: $!";
	exit if $pid;  # parent exits, child continues with new detached session
	(setsid() != -1)          or croak "can't start a new session: $!";
	open(STDERR, ">&STDOUT")  or croak "can't dup stderr -> stdout: $!";
	
	open(my $pf, '>', $pid_file);
	$pf->print($$);
	$pf->close;
}
