package SaveFile;

use strict;
use warnings;
use Carp;

use StringID;
use SFDate;
use SFCharModifier;
use SFChar;
use SFWarCB;
use SFWar;
use SFReader;


sub new {
	my $class = shift;
	my $filename = shift;
	
	my $self = bless
		{
			filename => $filename,
			date => undef,
			start_date => undef,
			chars => {},
			wars  => {},
			religions   => new StringID,
			cultures    => new StringID,
			job_titles  => new StringID,
			job_actions => new StringID,
			nicknames   => new StringID,
		}, $class;
	
	return $self;
}


sub parse {
	my $self = shift;
	
	open(my $fh, '<', $self->{filename}) or croak "failed to open: $!: $self->{filename}";
	
	$/ = "\r\n";
	
	my $f = SFReader->new($fh);
	
	# look for date
	while (defined(my $l = $f->next)) {
		if ($l =~ /^\tdate="([\d\.]+)"$/o) {
			$self->{date} = SFDate->new($1);
			last;
		}
	}
	
	# look for start_date
	while (defined(my $l = $f->next)) {
		if ($l =~ /^\tstart_date="([\d\.]+)"$/o) {
			$self->{start_date} = SFDate->new($1);
			last;
		}
	}
	
	croak "savegame lacks date: $self->{filename}" unless defined $self->{date};
	croak "savegame lacks start_date: $self->{filename}" unless defined $self->{start_date};
	
	# TODO: global flags
	
	# TODO: dynasties
	
	# look for character block start
	if ($f->search_for_line("\tcharacter=\r\n")) {
		#print STDERR "found character start block on line ", $f->line, "\n";
	}
		
	$f->getline; # eat a brace
	
	my $n_char_dead = 0;
	
	# now in the character block.  look for IDs, skip over following line (brace), parse object data.  repeat.
	
	my @IGNORED_KEYS = qw(
		birth_name
		name
		dna
		properties
		title
		ambition_date
		last_objective
		action_date
		moved_capital
		retinue_reinforce_rate
		spawned_bastards
		graphical_culture
		occluded
		death_reason
		killer
		ruler
		dynasty_named_title
	);
	
	my %ignore_key = map { $_ => 1 } @IGNORED_KEYS;
	
	while (my $l = $f->next) {
		if ($l =~ /^\t{2}(\d+)=$/o) { # begin character

			my $c = SFChar->new(
				id => 0+$1,
				female => 0,
				historical => 0,
				spouse => [],
				dynasty => 0, # should always be set even if 0, but just in case
				designated_heir => undef, # will be 0 by default for chars that it applies to
				death_date => undef, # only if dead
				guardian => undef,
				regent => undef,
				bastard => 0,
				pregnant => 0,
				prisoner => 0,
				consort => [],
				lover => [],
				claims => {}, # objects keyed by title name
				flags => {}, # SFDates keyed by flag name
				vars => {}, # numeric scalars keyed by variable name
				modifiers => {}, # objects keyed by modifier name
				);
		
			$f->getline; # eat brace
			
			# TODO: birth_name, name
			
			my $got_attr = 0;
			
			while (defined(my $l = $f->next)) {
				my ($k, $v);
				
				if ($l =~ /^\t{3}([a-z_]+)="([^"]+)"$/o) {
					($k, $v) = ($1, $2);
				}
				elsif ($l =~ /^\t{3}([a-z_]+)=(yes|no|\d+)$/o) {
					($k, $v) = ($1, $2);
				}
				elsif ($l =~ /^\t{3}attributes=$/o) {
					$got_attr = 1;
					# done with this section now
					last;
				}
				elsif ($l eq "\t\t}") {
					# end-of-character (unexpected...)
					croak "line ", $f->line, ": char ", $c->id, ": header: early termination!";
				}
				else {
					croak "line ", $f->line, ": char ", $c->id, ": header: unrecognized: $l";
				}
				
				if ($k eq 'birth_date') {
					$c->birth_date( SFDate->new($v) );
				}
				elsif ($k eq 'death_date') {
					$c->death_date( SFDate->new($v) );
					$c->old_holding([]);
					++$n_char_dead;
				}
				elsif ($k eq 'spouse') {
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
				elsif ($k eq 'nickname') {
					$c->nickname( $self->{nicknames}->id($v) );
				}
				elsif (exists $ignore_key{$k}) {
					# skip
				}
				else {
					croak "line ", $f->line, ": char ", $c->id, ": header: unrecognized key=val{sbi}: $k: $v";
				}
			}

			# finalize required variables from previous section
			if (!defined $c->birth_date) {
				croak "line ", $f->line, ": char ", $c->id, ": no birthdate defined!";
			}
			
			croak "no attrs, just EOF" if (!$got_attr);
			
			# attributes section had just gotten started
			$f->getline; # eat brace
			
			# next line is pointing at attribute value list
			my $attr_line = $f->getline;
			$attr_line =~ s/[\s\r}]+$//o;
			my @attrs = split(' ', $attr_line);
			$c->base_diplomacy($attrs[0]);
			$c->base_martial($attrs[1]);
			$c->base_stewardship($attrs[2]);
			$c->base_intrigue($attrs[3]);
			$c->base_learning($attrs[4]);
			
			# consume key-values up to a ledger= block, flags block, variables block, modifiers block,
			# or close of the character block.
			
			# detect the optional demesne= block and handle it within the same traversal through use
			# of a helper method (and others).

			while (defined(my $l = $f->next)) {
				my ($k, $v);
				
				if ($l =~ /^\t{3}([a-z_]+)=(-?\d+\.\d+)$/o) {
					($k, $v) = ($1, 0+$2);
				}
				elsif ($l =~ /^\t{3}([a-z_]+)="([^"]+)"$/o) {
					($k, $v) = ($1, $2);
					
					if ($k eq 'religion') {
						$c->religion( $self->{religions}->id($v) );
					}
					elsif ($k eq 'culture') {
						$c->culture( $self->{cultures}->id($v) );
					}
					elsif ($k eq 'job_title') {
						$c->job_title( $self->{job_titles}->id($v) );
					}
					elsif ($k eq 'action') {
						$c->job_action( $self->{job_actions}->id($v) );
					}
					elsif ($k eq 'old_holding') {
						push @{$c->old_holding}, $v;
					}
					elsif ($k eq 'imprisoned') {
						$c->imprison_date( SFDate->new($v) )
					}
					elsif (exists $ignore_key{$k}) {
						# skip
					}
					else {
						croak "line ", $f->line, ": char ", $c->id, ": main: unrecognized key=val{s}: $k: $v";
					}
				}
				elsif ($l =~ /^\t{3}([a-z_]+)=(\d+)$/o) {
					($k, $v) = ($1, 0+$2);
					
					if ($k eq 'employer') {
						$c->employer($v);
					}
					elsif ($k eq 'host') {
						$c->host($v);
					}
					elsif ($k eq 'dynasty') {
						$c->dynasty($v);
					}
					elsif ($k eq 'guardian') {
						$c->guardian($v);
					}
					elsif ($k eq 'regent') {
						$c->regent($v);
					}
					elsif ($k eq 'betrothal') {
						$c->betrothed($v);
					}
					elsif ($k eq 'consort') {
						push @{$c->consort}, $v;
					}
					elsif ($k eq 'lover') {
						push @{$c->lover}, $v;
					}
					elsif ($k eq 'designated_heir') {
						$c->designated_heir($v);
					}
					elsif ($k eq 'action_location') {
						$c->job_action_location($v);
					}
					elsif (exists $ignore_key{$k}) {
						# skip
					}
					else {
						croak "line ", $f->line, ": char ", $c->id, ": main: unrecognized key=val{i}: $k: $v";
					}
				}
				elsif ($l =~ /^\t{3}([a-z_]+)=(yes|no)$/o) {
					($k, $v) = ($1, ($2 eq 'yes') ? 1 : 0);
					
					if ($k eq 'is_bastard') {
						$c->bastard($v);
					}
					elsif ($k eq 'is_prisoner') {
						$c->prisoner($v);
					}
					elsif (exists $ignore_key{$k}) {
						# skip
					}
					else {
						croak "line ", $f->line, ": char ", $c->id, ": main: unrecognized key=val{b}: $k: $v";
					}
				}
				elsif ($l =~ /^\t{3}type=[a-z]+$/o) {
					# skip: not sure, but I think: character types for non-feudal dead characters.
				}
				elsif ($l eq "\t\t\ttraits=") {
					$f->getline; # eat a brace
					my $trait_line = $f->getline;
					$trait_line =~ s/[\s\r}]+$//o;
					$c->traits( { map { 0+$_ => 1 } split(' ', $trait_line) } );
				}
				elsif ($l eq "\t\t\tunborn=") {
					$c->pregnant(1);
					$f->search_for_line("\t\t\t}\r\n");
				}
				elsif ($l eq "\t\t\tknown_plots=") {
					$f->getline;
					$f->getline;
				}
				elsif ($l eq "\t\t\tclaim=") {
					$self->_parse_char_claim_single($c, $f);
				}
				elsif ($l eq "\t\t\tdemesne=") {
					$self->_parse_char_demesne($c, $f);
				}
				elsif ($l eq "\t\t\tledger=") {
					$f->search_for_line("\t\t\t}\r\n");
				}
				elsif ($l eq "\t\t\tflags=") {
					$self->_parse_char_flags($c, $f);
				}
				elsif ($l eq "\t\t\tvariables=") {
					$self->_parse_char_vars($c, $f);
				}
				elsif ($l eq "\t\t\tmodifier=") {
					$self->_parse_char_modifier_single($c, $f);
				}
				elsif ($l eq "\t\t\tcharacter_action=") {
					$f->search_for_line("\t\t\t}\r\n");
				}
				elsif ($l eq "\t\t\telector_funds=") {
					$f->getline;
					$f->getline;
					$f->getline;
					$f->getline;
				}
				elsif ($l eq "\t\t}") {
					# end-of-character
					last;
				}
				else {
					croak "line ", $f->line, ": char ", $c->id, ": main: unrecognized: $l";
				}
			}
			
			# commit character object to savefile-global map
			$self->{chars}{ $c->id } = $c;
		}
		elsif ($l eq "\t}") {
			# end of character block.
			last;
		}
	}
	
	while ($f->search_for_line("\tactive_war=\r\n")) {
	
		my $w = new SFWar;
	
		$f->getline;
	
		while (defined(my $l = $f->next)) {
			if ($l =~ /^\t{2}name="([^"]+)"$/o) {
				$w->name($1);
			}
			elsif ($l =~ /^\t{2}(attacker|defender)=(\d+)$/o) {
				my ($k, $v) = ($1, 0+$2);
				if ($k eq 'attacker') {
					push @{$w->attackers}, $v;
				}
				else {
					push @{$w->defenders}, $v;
				}
			}
			elsif ($l eq "\t\tcasus_belli=") {
				$f->getline;
				
				my $cb = new SFWarCB;
				
				my ($k, $v);
				while (defined(my $l = $f->next)) {
					if ($l =~ /^\t{3}([a-z_]+)="([^"]+)"$/o) {
						($k, $v) = ($1, $2);
						
						if ($k eq 'casus_belli') {
							$cb->name($v);
						}
						elsif ($k eq 'landed_title') {
							$cb->landed_title($v);
						}
						elsif ($k eq 'date') {
							# skip
						}
						else {
							croak "line ", $f->line, ": active_war '", $w->name, "': cb: unrecognized key=val{s}: $k: $v";
						}
					}
					elsif ($l =~ /^\t{3}([a-z_]+)=(\d+)$/o) {
						my ($k, $v) = ($1, 0+$2);
						if ($k eq 'actor') {
							$cb->actor($v);
						}
						elsif ($k eq 'recipient') {
							$cb->recipient($v);
						}
						elsif ($k eq 'thirdparty') {
							$cb->thirdparty($v);
						}
						else {
							croak "line ", $f->line, ": active_war '", $w->name, "': cb: unrecognized key=val{i}: $k: $v";
						}
					}
					elsif ($l eq "\t\t}") {
						# end-of-CB
						$w->casus_belli($cb);
						last;
					}
					else {
						croak "line ", $f->line, ": active_war '", $w->name, "': cb: unrecognized: $l";
					}
				}
			}
			elsif ($l eq "\t}") {
				# end-of-war
				$self->{wars}{ $w->name } = $w;
				last;
			}
			else {
				# skip (history)
				# TODO: important to parse history for start date of war and the actual, current attacker / defender list
				# warscore, participation, and vassal-liege relations are not very important
			}
		}
	}
	
	# done with file
	$f->handle->close;
}


sub _parse_char_claim_single {
	my ($self, $c, $f) = @_;

	$f->getline; # eat brace
	$f->search_for_line("\t\t\t}\r\n");
}


sub _parse_char_demesne {
	my ($self, $c, $f) = @_;

	$f->getline; # eat brace
	$f->search_for_line("\t\t\t}\r\n");
}


sub _parse_char_flags {
	my ($self, $c, $f) = @_;

	$f->getline; # eat brace

	while (defined(my $l = $f->next)) {
		if ($l =~ /^\t{4}([0-9a-zA-Z_\.\-]+)=([\d\.]+)$/o) {
			$c->flags($1, SFDate->new($2))
		}
		elsif ($l =~ /^\t{3}[}]$/o) {
			# end of flags list
			last;
		}
		else {
			croak;
		}
	}
}


sub _parse_char_vars {
	my ($self, $c, $f) = @_;

	$f->getline; # eat brace

	while (defined(my $l = $f->next)) {		
		if ($l =~ /^\t{4}([0-9a-zA-Z_\.\-]+)=(-?\d+)\.(\d{3})$/o) {
			my ($key, $val_int, $val_dec) = ($1, $2, $3);
			my $val = (!$val_dec || $val_dec eq '000') ? 0+$val_int : $val_int+$val_dec/1000;
			$c->vars($key, $val);
		}
		elsif ($l =~ /^\t{3}[}]$/o) {
			# end of variable table
			last;
		}
		else {
			croak "line ", $f->line, ": char: vars: unrecognized: $l\n";
		}
	}
}


sub _parse_char_modifier_single {
	my ($self, $c, $f) = @_;

	my $m = SFCharModifier->new;
	$f->getline or croak; # eat brace

	my $v = $f->getline or croak;
	$v =~ /^\t{4}modifier="([^"]+)"\r$/o or croak;
	$m->name($1);
	
	$v = $f->getline or croak;
	$v =~ /^\t{4}date="([^"]+)"\r$/o or croak;
	$m->date( SFDate->new($1) ); # unsure of how to interpret the dates encoded here
	
	$v = $f->getline or croak;
	$v =~ /^\t{4}inherit=(yes|no)\r$/o or croak;
	$m->inherit( ($1 eq 'yes') ? 1 : 0 );
	
	$v = $f->getline or croak;
	$v =~ /^\t{4}hidden=(yes|no)\r$/o or croak;
	$m->hidden( ($1 eq 'yes') ? 1 : 0 );
	
	$f->getline or croak; # eat brace
	$c->modifiers($m->name, $m);
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


sub wars {
	my $self = shift;
	return $self->{wars};
}


1;
