package CK2SaveFile;

use strict;
use warnings;
use Carp;

sub new {
	my $class = shift;
	my $filename = shift;
	
	my $self = bless
		{
			filename => $filename,
			date => undef,
			start_date => undef,
			chars => {},
		}, $class;
	
	return $self;
}


sub parse {
	my $self = shift;
	
	open(my $f, '<', $self->{filename}) or croak "$!: $self->{filename}";
	
	$/ = "\r\n";
	
	# look for date
	while (<$f>) {
		chomp;
		
		if (/^\tdate="([\d\.]+)"$/o) {
			$self->{date} = $1;
			last;
		}
	}
	
	# look for start_date
	while (<$f>) {
		chomp;
		
		if (/^\tstart_date="([\d\.]+)"$/o) {
			$self->{start_date} = $1;
			last;
		}
	}
	
	croak "savegame lacks date: $self->{filename}" unless defined $self->{date};
	croak "savegame lacks start_date: $self->{filename}" unless defined $self->{start_date};
	
	# TODO: global flags
	
	# TODO: dynasties
	
	# look for character block start
	
	while (<$f>) {
		chomp;
		last if (/^\tcharacter=$/o);
	}
	
	print STDERR " [char block]\n";
		
	<$f>; # eat a brace
	
	my $n_char_dead = 0;
	
	# now in the character block.  look for IDs, skip over following line (brace), parse object data.  repeat.
	
	while (my $l = <$f>) {

		chomp $l;
		
		if ($l =~ /^\t{2}(\d+)=$/o) { # begin character

			my %char = (
				id => 0+$1,
				dob => undef,
				traits => undef,
				vars => {}
				);
		
			print STDERR "  [char object] ID: $char{id}\n";
		
			<$f>; # eat brace
			
			# TODO: birth_name, name
			
			# get birth_date and optionally death_date
			
			while (my $l = <$f>) {
				chomp $l;
				
				my ($k, $v);
				
				if ($l =~ /^\t{3}([a-z_]+)="([^"]+)"$/o) {
					($k, $v) = ($1, $2);
				}
				elsif ($l =~ /^\t{3}([a-z_]+)=(yes|no|\d+)$/o) {
					($k, $v) = ($1, $2);
				}
				else {
					# advanced past target section (file ptr advanced over attributes list sentinel, now pointing at beginning of value list)
					last;
				}
				
				if ($k eq 'birth_date') {
					$char{dob} = $v;
					print STDERR "   [birth] $v\n";
				}
				elsif ($k eq 'death_date') {
					$char{dod} = $v;
					++$n_char_dead;
					print STDERR "   [death] $v\n";
				}
				elsif (!defined $k || !defined $v) {
					croak "something went wrong: key=$k, val=$v";
				}
				else {
					# currently don't care but this includes father, mother, real_father (?), spouse(s), liege, killer, death_reason, name, and birth_name (at least)
				}
			}

			if (!defined $char{dob}) {
				croak "character object without birth_date (ID $char{id}, file $self->{filename})";
			}
			
			# TODO: attributes (currently, next line is pointing at their value list)
			
			# skip to traits
			while (my $l = <$f>) {
				chomp $l;
				
				if ($l =~ /^\t{3}traits=$/o) {
					<$f>; # eat brace
					
					my $trait_line = <$f>;
					chomp $trait_line;
					
					$trait_line =~ s/[\s}]+$//;

					print STDERR "   [traits] $trait_line\n";
					
					my %traits = map { 0+$_ => 1 } split(' ', $trait_line);
	
					$char{traits} = \%traits;
					
					last; # no more traits for this character
				}
				else {
					# print STDERR "   [no match] $l\n";
				}
			}
		
			# TODO: character flags
			
			# skip to (optional) variables
			while (my $l = <$f>) {
				chomp $l;
				
				my $vars_done = 0;
				
				if (!$vars_done && $l =~ /^\t{3}variables=$/o) {
					<$f>; # eat brace
					
					print STDERR "   [var list]\n";
					
					while (my $l = <$f>) {
						chomp $l;
						
						if ($l =~ /^\t{4}([0-9a-zA-Z_\.\-]+)=(\d+)\.(\d{3})$/o) {
							my ($key, $val_int, $val_dec) = ($1, $2, $3);
							my $val = (!$val_dec || $val_dec eq '000') ? 0+$val_int : $val_int+$val_dec/1000;
							$char{vars}{$key} = $val;
							
							print STDERR "    [$key] $val\n";
						}
						elsif ($l =~ /^\t{3}[}]$/o) {
							# end of variable table
							$vars_done = 1;
							print STDERR "   [/var list]\n";
							last;
						}
					}
				}
				elsif ($l =~ /^\t{2}[}]$/o) {
					# end of character object.
					last;
				}
				
				# NOTE: after variables and before closing the character object, of future interest, is the modifier list
			}
			
			# commit character object to savefile-global map
			$self->{chars}{ $char{id} } = \%char;
			
			print STDERR "  [/char]\n";
		}
		elsif ($l =~ /^\t[}]$/o) {
			print STDERR " [/char block]\n";
			# end of character block.
			last;
		}
	}
	
	# done with file
	$f->close;
}


sub start_date {
	my $self = shift;
	return $self->{start_date};
}


sub date {
	my $self = shift;
	return $self->{date};
}


sub chars {
	my $self = shift;
	return $self->{chars};
}


1;
