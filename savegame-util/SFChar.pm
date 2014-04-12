package SFChar;

use StringID;
use SFDate;
use Class::Struct;

struct 'SFChar' => [
    id => '$',
    birth_date => 'SFDate',
    death_date => 'SFDate',
	nickname => '$', # encoded by StringID
    mother => '$',
    father => '$',
    real_father => '$',
    historical => '$',
    spouse => '@',
	betrothed => '$',
    female => '$',
	pregnant => '$',
    liege => '$',
	base_diplomacy => '$',
	base_martial => '$',
	base_stewardship => '$',
	base_intrigue => '$',
	base_learning => '$',
	traits => '%',
	job_title => '$', # encoded by StringID
	religion => '$', # encoded by StringID
	culture => '$', # encoded by StringID
	job_action => '$', # encoded by StringID, renamed from action key in file format
	job_action_location => '$', # province ID, renamed from action_location key in file format
	dynasty => '$',
	consort => '@',
	lover => '@',
	bastard => '$', # renamed from is_bastard key in file format
	designated_heir => '$',
	fertility => '$',
	health => '$',
	prestige => '$',
	piety => '$',
	claims => '%',
	capital => '$',
	primary => '$',
	peace_months => '$',
	wealth => '$',
	monthly_income => '$',
	monthly_expense => '$',
	averaged_income => '$',
    employer => '$',
    host => '$',
	prisoner => '$', # renamed from is_prisoner key in file format
	imprison_date => 'SFDate',
	guardian => '$',
	regent => '$',
    old_holding => '@',
	flags => '%',
	vars => '%',
	modifiers => '%',
];

1;

