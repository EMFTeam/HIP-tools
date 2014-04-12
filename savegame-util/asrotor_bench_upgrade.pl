#!/usr/bin/perl

# quick script to upgrade the benchmark file format

use strict;
use warnings;

use Carp;
use File::Spec;
use File::Copy;

my $archive_base_dir = "/cygdrive/c/Users/$ENV{USER}/Documents/asrotor";
chdir($archive_base_dir) or croak "chdir: $!: $archive_base_dir";
opendir my $abd, '.' or croak "opendir: $!";

my @series = grep { $_ !~ /^\./ && -d $_ } readdir($abd);

for my $s (@series) {
    print "$s ...\n";

    my $bfile = File::Spec->catfile($s, "benchmark_${s}.csv");

    unless (-f $bfile) {
	print "  no benchmark file found.\n";
	next;
    }

    my $bofile = $bfile.".tmp";

    open(my $bfo, '>', $bofile) or croak "open: $!: $bofile";
    open(my $bfi, '<', $bfile)  or croak "open: $!: $bfile";

    $bfo->print("Relative Year;Duration (seconds);File Size (MB);Resume Reason;Comment\n");
    <$bfi>;

    while (<$bfi>) {
	chomp;
	$bfo->print("$_;;\n") if $_;
    }

    $bfi->close;
    $bfo->close;

    File::Copy::move($bfile, $bfile.".bak");
    File::Copy::move($bofile, $bfile);

    print "  [done] $bfile\n";
}

exit 0;
