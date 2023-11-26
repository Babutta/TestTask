#!/usr/bin/perl
#
# Парсит данные из лога и ищет по адресу
#

use strict;
use utf8;

use DBI;
use JSON;
use CGI::WebIn;

my $dsn = "DBI:mysql:testtask";
my $username = "...";
my $password = '...';

my $dbh = DBI->connect($dsn, $username, $password);

if ($IN{ajax}) {
	print "Content-type: application/json; charset=utf-8\n\n";

	if ($IN{search}) {
		my $data = $dbh->selectall_arrayref("SELECT SQL_CALC_FOUND_ROWS created,str FROM (
		(SELECT int_id,created,str FROM `log` WHERE `address` = ?)
		UNION ALL
		(SELECT int_id,created,str FROM `message` WHERE `str` REGEXP ?)
		) AS ut
		ORDER BY int_id ASC, created ASC
		LIMIT 100", undef, $IN{search}, '[[:<:]]' . $IN{search} . '[[:>:]]');

		my $result = { search => $IN{search}, found => $data };

		if (scalar(@$data) == 100) {
			($result->{total}) = $dbh->selectrow_array("SELECT FOUND_ROWS()");
		} else {
			$result->{total} = scalar(@$data);
		}

		my $json = JSON->new->allow_nonref;

		print $json->encode($result);
	}
	else {
		print "{}";
	}
}
elsif ($ARGV[0] && $ARGV[0] eq 'parse') {
	open(LOG, "../tmp/out") || die("Can't open log file");

	$dbh->do("TRUNCATE `log`");
	$dbh->do("TRUNCATE `message`");

	while (my $str = <LOG>) {
		if ($str =~ /^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+((\S{16})\s+(\S+)\s*([^\s:]+\@[^\s:]+)?(.*))$/) {
			my $created = $1;
			my $log_str = $2;
			my $int_id = $3;
			my $status = $4;
			my $address = $5;
			my $str = $6;

			if ($status eq '<=') {
				if ($str && $str =~ /\sid\=(\S+)/) {
					my $id = $1;

					$dbh->do("INSERT INTO `message` SET `created`=?,`id`=?,`int_id`=?,`str`=?", undef, $created, $id, $int_id, $log_str);
				}
			}
			else {
				$dbh->do("INSERT INTO `log` SET `created`=?,`address`=?,`int_id`=?,`str`=?", undef, $created, $address, $int_id, $log_str);
			}
		}
	}
	close(LOG);
}


