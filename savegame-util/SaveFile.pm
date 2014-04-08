package SaveFile;

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

			my $c = SFChar->new(
				id => 0+$1,
				female => 0,
				historical => 0,
				dynasty => 0,
				death_date => undef,
				);
		
			print STDERR "  [char object] ID: ", $c->id, "\n";
		
			<$f>; # eat brace
			
			# TODO: birth_name, name
			
			while (my $l = <$f>) {
				chomp $l;
				
				my ($k, $v);
				
				if ($l =~ /^\t{3}([a-z_]+)="([^"]+)"$/o) {
					($k, $v) = ($1, $2);
				}
				elsif ($l =~ /^\t{3}([a-z_]+)=(yes|no|\d+)$/o) {
					($k, $v) = ($1, $2);
				}
				elsif ($l =~ /^\t{3}attributes=$/o) {
					# done with this section now
					last;
				}
				else {
					croak;
				}
				
				if ($k eq 'birth_date') {
					$c->birth_date($v);
				}
				elsif ($k eq 'death_date') {
					$c->death_date($v);
					++$n_char_dead;
				}
				elsif ($k eq 'spouse')
					push @{$c->spouse}, 0+$v;
				}
				elsif ($k eq 'female') {
					$c->female(1);
				}
				elsif ($k eq 'father') {
					$c->father(0+$v);
				}
				elsif ($k eq 'real_father') {
					$c->real_father(0+$v);
				}
				elsif ($k eq 'mother') {
					$c->mother(0+$v);
				}
				elsif ($k eq 'liege') {
					# only happens for dead characters in actual character definition.
					# has to be derived from held title lieges, for living characters.
					# I assume it was the character's liege at time of death...
					$c->liege(0+$v);
				}
				elsif ($k eq 'historical') {
					$c->historical(1);
				}
			}

			# finalize required variables from previous section
			if (!defined $c->birth_date) {
				croak "character object without birth_date (ID ", $c->id, ", file $self->{filename})";
			}
			
			# attributes section had just gotten started
			<$f>; # eat brace
			
			# next line is pointing at attribute value list
			my $attr_line = <$f>
			$attr_line =~ s/[\s\r}]+$//;
			@attrs = split(' ', $attr_line);
			$c->base_diplomacy($attrs[0]);
			$c->base_martial($attrs[1]);
			$c->base_stewardship($attrs[2]);
			$c->base_intrigue($attrs[3]);
			$c->base_learning($attrs[4]);
			
			# now straight to traits
			if ($l =~ /^\t{3}traits=$/o) {
				
				my $trait_line = <$f>;
				$trait_line =~ s/[\s\r}]+$//;
				%{$c->traits} = map { 0+$_ => 1 } ;
				
				last;
			}
			else {
				croak;
			}
			
			# consume key-values up to a demesne= or wealth=<num> or close of the character block (dead guys)
			# detect demesne= blocks and call a helper routine to read those

			while (my $l = <$f>) {
				chomp $l;
				
				my ($k, $v);
				
				if ($l =~ /^\t{3}([a-z_]+)=(-?\d+)\.(\d{5})$/o) {
					($k, $v) = ($1, 0+$2 + $3/10_000);
					last;
				}
				elsif ($l =~ /^\t{3}([a-z_]+)=(-?\d+)\.(\d{3})$/o) {
					($k, $v) = ($1, 0+$2 + $3/1000);
					last;
				}
				elsif ($l =~ /^\t{3}([a-z_]+)="([^"]+)"$/o) {
					($k, $v) = ($1, $2);
				}
				elsif ($l =~ /^\t{2}[}]$/o) {
					last;
				}
			}
			
			# TODO: character flags
			
			$self->_parse_char_vars($c, $f);
			
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


sub _parse_char_vars {
	my ($self, $c, $f) = @_;
	
	# skip to (optional) variables
	while (my $l = <$f>) {
		chomp $l;
		
		my $vars_done = 0;
		
		if (!$vars_done && $l =~ /^\t{3}variables=$/o) {
			<$f>; # eat brace

			while (my $l = <$f>) {
				chomp $l;
				
				if ($l =~ /^\t{4}([0-9a-zA-Z_\.\-]+)=(\d+)\.(\d{3})$/o) {
					my ($key, $val_int, $val_dec) = ($1, $2, $3);
					my $val = (!$val_dec || $val_dec eq '000') ? 0+$val_int : $val_int+$val_dec/1000;
					$c->vars($key, $val);
				}
				elsif ($l =~ /^\t{3}[}]$/o) {
					# end of variable table
					$vars_done = 1;
					last;
				}
			}
		}
		elsif ($l =~ /^\t{2}[}]$/o) {
			# end of character object.
			return 0;
		}
		
		# NOTE: after variables and before closing the character object, of future interest, is the modifier list
	}
	
	return 1;
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
