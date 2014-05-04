#!/usr/bin/perl

use strict;
use warnings;
use Carp;
use Getopt::Long qw(:config gnu_getopt);
use File::Spec;
use Data::Dumper;
use File::Basename qw(basename);

my $GIT_BIN = '/usr/bin/git';
my $MIN_EVENT_ID_TO_REALLOCATE = 500_000;

my $vanilla_events_dir = "/cygdrive/c/Program Files (x86)/Steam/SteamApps/common/Crusader Kings II/events";
my $base_dir = "/cygdrive/c/Users/Stark/Documents/GitHub/VIET";
my @mod_dirs = qw( VIET_Immersion/common VIET_Immersion/vanilla VIET_Immersion/PB VIET_Events PB_VIET_Events );

#my $mod_decisions_dir = File::Spec->catdir($mod_dir, "decisions");
#my $mod_actions_file = File::Spec->catdir($mod_dir, "common/on_actions/00_on_actions.txt");


my $opt_namespace = 'VIETnam';
my $opt_offset = 0;

# Switch current working directory to the mods' base directory
chdir $base_dir or croak "could not change working directory: $!: $base_dir";

# Load vanilla event filename blacklist for ID reallocation, load event filenames
# from mods, filter out any blacklist matches from the latter.

my %evt_file_blacklist = map { $_ => 1 } load_txt_filenames($vanilla_events_dir);

my @evt_files = (); # Full paths to files rather than just basenames

for my $mod_dir (@mod_dirs) {
	my $mod_events_dir = File::Spec->catdir($mod_dir, "events");
	next unless -e $mod_events_dir; # Not all of the mods contain events!
	
	push @evt_files,
		map { File::Spec->catfile($mod_events_dir, $_) }
		grep { !exists $evt_file_blacklist{$_} }
		load_txt_filenames($mod_events_dir);
}

# Maps numeric event IDs defined in event files to their source and, later, their new ID
my %evt = ();

# Scan all event files for numerically IDed event definitions
for my $evt_file (@evt_files) {
	parse_event_file($evt_file, \%evt);
}

print Dumper(\%evt);
print scalar keys %evt, "\n";

# Allocate namespaced IDs for all of the qualifying numerically IDed events

# We use a single namespace $opt_namespace, and we start numbering from $opt_offset.
# We do not group IDs into blocks within the namespace for maximum allocation
# efficiency, but we do first sort them numerically by original ID so that events
# which were allocated numerically 'nearby' or in order remain so within the namespace.

my $nid = $opt_offset;
my @sorted_evt = sort { $a->{id} <=> $b->{id} } values %evt;

for my $evt (@sorted_evt) {
	$evt->{nid} = $opt_namespace.'.'.$nid++;
	my $short_file = basename($evt->{file}, '.txt');
	$evt->{msg} = "Map event $evt->{id} to $evt->{nid} ($short_file)";
}

# Finally, we pretty much do a search and replace, except we're careful to make sure
# that we match only against full tokens (not parts of them). This could, of course,
# result in some rare (nonexistent) cases of replacing a circumstantially identical
# numeric ID of another type (such as character or dynasty), but we limit the renaming
# to common/on_actions, common/cb_types, common/objectives, decisions/, and events/,
# so this is particularly unlikely and should be very easy to identify/fix if it does
# occur.  Thus, I'm not going to the [admittedly minor] trouble to make sure that each
# numeric ID matched outside of on_actions is preceded by a token sequence of 'id' and
# '=', which would prevent all possible collisions with other types of integers. If this
# were extended to cover character or title history, that'd definitely be a requirement,
# however.

my @subdirs = qw( common/on_actions common/cb_types common/objectives decisions events );
my $num_evt = scalar @sorted_evt;
my $n = 0;

for my $evt (@sorted_evt) {
	++$n;
	
	print STDERR "[$n/$num_evt] $evt->{msg}\n";

	for my $mod_dir (@mod_dirs) {
		for my $dir (@subdirs) {
			my $path = File::Spec->catdir($mod_dir, $dir);
			next unless -e $path;
			
			for my $filename ( load_txt_filenames($path) ) {
				rename_event($evt, File::Spec->catfile($path, $filename));
			}
		}
	}
	
	commit_rewrite($evt);
}


exit 0;


sub load_txt_filenames {
	my $dir = shift;
	opendir(my $d, $dir) or croak "opendir: $!: $dir";
	return sort grep { /\.txt$/ } readdir $d;
}


sub parse_event_file {
	my $file = shift;
	my $events = shift;
	
	open(my $f, '<', $file) or croak "failed to open event file: $!: $file";
	my $n_line = 0;
	
	while (<$f>) {
		++$n_line;
		
		next if /^\s*\#/;
		next unless /\{/;
		
		# at top-level & current line contains at least one opening brace
		
		my $type;
		
		if (/^\s*(character|letter|narrative|province)_event\s*=\s*\{\s*$/) {
			# well-formed event definition opening line
			$type = $1;
		}
		else {
			parse_err($file, $n_line, "failed to recognize event definition opening statement");
		}
		
		# we're now at brace nest level 1, directly inside an event definition.
		# parse everything we want from the event and only return here once the file pointer is
		# advanced to the line or EOF following its final closing brace.
		
		$n_line = parse_event($f, $file, $n_line, $type, $events);
	}
}


sub parse_event {
	my $f = shift;
	my $file = shift;
	my $n_line = shift;
	my $type = shift;
	my $events = shift;
	
	# file pointer for $f is at the line following an, e.g., 'character_event = {' statement.

	my $start_line = $n_line;
	
	# scan lines looking for an event ID.  we assume no blocks (braces) are ever valid before
	# we find the ID.
	
	my $id;
	
	while (<$f>) {
		++$n_line;

		next if /^\s*\#/;
		
		if (/^\s*id\s*=\s*([a-zA-Z0-9_\.\-]+)\s*(?:\#[^\r]*)?\r?$/) {
			# found an ID!
			$id = $1;
		}
		elsif (/^[^#]*[}{]/) {
			# something bad happened.  a brace was found before an ID.
			parse_err($file, $n_line, "found bracket(s) before ID in event definition starting at line $start_line");
		}
		else {
			# just skip whatever it is, since we're guaranteed by the prior case
			# that we won't leave the event definition.
			next;
		}

		# we found an ID. was it strictly an integer numeric (legacy)?
		
		if ($id =~ /^(\d+)$/) {
			# it was.
			
			$id = 0+$id;
			
			if ($id >= $MIN_EVENT_ID_TO_REALLOCATE) {
			
				if (exists $events->{$id}) {
					# hmm? well, not an error case. not only can events be redefined in the same mod, but
					# we're spanning multiple [related] mods. since ultimately we're just going to rename
					# the event and every reference to it with the same name, it'll still be consistent
					# for our purposes. a warning would be nice, though.
					
					print STDERR "info: event $id defined again in file '$file' at line $start_line\n";
				}
				
				$events->{$id} = { id => $id, file => $file, line => $start_line };
			}
			else {
				print STDERR "info: event ID too low for reallocation: $id ($file:$start_line)\n";
			}
		}
		
		# now, we need to consume the rest of the event syntactically.  that means matching opening
		# and closing braces until our nest level is 0 (one more closing brace than opening, as that
		# accounts for the opening brace which started the event definition.
		
		return consume_event($f, $file, $n_line, $start_line, $id);
	}
	
	parse_err($file, $n_line, "unexpected EOF while still in event starting at line $start_line");
}


sub consume_event {
	my $f = shift;
	my $file = shift;
	my $n_line = shift;
	my $start_line = shift;
	my $id = shift;
	
	my $nest = 1;
	
	while (<$f>) {
		++$n_line;
		
		next if /^\s*\#/;
		
		# could definitely be a lot more terse with validation here, but whatever.
		
		while (/([}{#])/g) {
			last if $1 eq '#';
		
			$nest += ($1 eq '{');
			$nest -= ($1 eq '}');
			
			parse_err($file, $n_line, "too many closing braces for event $id: starts at line $start_line")
				if $nest < 0;
		}
		
		last unless $nest > 0;
	}
	
	parse_err($file, $n_line, "unexpected EOF in event $id: starts at line $start_line")
		if $nest > 0;
	
	return $n_line;
}


sub commit_rewrite {
	my $evt = shift;
	
	my @cmd = ($GIT_BIN, 'commit', '-a', '-m', $evt->{msg});
	(system(@cmd) == 0) or croak "git failed to commit: exit code: ".($? >> 8);
}


sub rename_event {
	my $evt = shift;
	my $file = shift;

	my $text;

	{
		open(my $f, '<', $file) or croak "failed to open file: $!: $file";
		local $/; # localized slurp
		$text = <$f>;
		close $f;
	}

	return unless $text; # Plenty of blank files around these parts...

	my $dirty = $text =~ s/\b$evt->{id}\b/$evt->{nid}/sg;
	
	if ($dirty) {
		# As we did, in fact, find references to the legacy event ID and replace them
		# within $text with the new ID, we now write the modified text back to its
		# source file.
		
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
