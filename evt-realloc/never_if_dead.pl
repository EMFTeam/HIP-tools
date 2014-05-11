#!/usr/bin/perl

# Quick hack of preexisting evrealloc.pl code which literally does just a
# 'token' search/replace for [father|mother]_even_if_dead and fixes the scopes.
# A 'token' S/R is one that matches at whole word boundaries only.

use strict;
use warnings;
use Carp;
use File::Spec;
use Data::Dumper;

my $vanilla_events_dir = "/cygdrive/c/Program Files (x86)/Steam/SteamApps/common/Crusader Kings II/events";
my $base_dir = "/cygdrive/c/Users/Stark/Documents/GitHub/VIET";
my @mod_dirs = qw( VIET_Immersion/common VIET_Immersion/vanilla VIET_Immersion/PB VIET_Events PB_VIET_Events );
my @subdirs = qw( common/minor_titles common/landed_titles common/nicknames common/landed_titles common/cb_types common/objectives decisions events history/characters );

# Switch current working directory to the mods' base directory
chdir $base_dir or croak "could not change working directory: $!: $base_dir";

my $n = 0;

for my $mod_dir (@mod_dirs) {
	for my $dir (@subdirs) {
		my $path = File::Spec->catdir($mod_dir, $dir);
		next unless -e $path;
		
		for my $filename ( load_txt_filenames($path) ) {
			rename_words( File::Spec->catfile($path, $filename) );
		}
	}
}


exit 0;


sub load_txt_filenames {
	my $dir = shift;
	opendir(my $d, $dir) or croak "opendir: $!: $dir";
	return sort grep { /\.txt$/ } readdir $d;
}


# never_if_dead
sub rename_words {
	my $file = shift;

	my $text;

	{
		open(my $f, '<', $file) or croak "failed to open file: $!: $file";
		local $/; # localized slurp
		$text = <$f>;
		close $f;
	}

	return unless $text; # Plenty of blank files around these parts...

	my $dirty = $text =~ s/\bfather_even_if_dead\b/father/sgi;
	$dirty += $text =~ s/\bmother_even_if_dead\b/mother/sgi;
	
	if ($dirty) {
		print STDERR "  [", '#' x $dirty, "]  $file\n";
		
		open(my $f, '>', $file) or croak "failed to open file for rewrite: $!: $file";
		$f->print($text);
		close $f;
	}
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
