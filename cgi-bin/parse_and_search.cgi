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
my $username = "testtask_user";
my $password = 'pwU2jXL1aMG7c2H5OKcX';

my $dbh = DBI->connect($dsn, $username, $password);
if ($ARGV[0] eq 'parse') {
    open(LOG, "../tmp/out") || die("Can't open log file");

    $dbh->do("TRUNCATE `log`");
    $dbh->do("TRUNCATE `message`");

    while (my $line = <LOG>) {
        my ($created, $log_str, $int_id, $flag, $email, $str) = $line =~ /^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+((\S{16})\s+(\S+)\s*([^\s:]+\@[^\s:]+)?(.*))$/;

        next unless $str;

        if ($flag eq '<=') {
            my ($id) = $str =~ /\sid\=(\S+)/;

            $dbh->do("INSERT INTO `message` SET `created`=?,`id`=?,`int_id`=?,`str`=?", undef, $created, $id, $int_id, $log_str);
        }
        else {
            $dbh->do("INSERT INTO `log` SET `created`=?,`address`=?,`int_id`=?,`str`=?", undef, $created, $email, $int_id, $log_str);
        }
    }

    close(LOG);
}
else {
    my $search = $IN{search};
    my $message = '';
    my $result = '';

    $search =~ s/^\s+|\s+$//g;

    if ($search) {
        my $total = 0;

        my $data = $dbh->selectall_arrayref("SELECT SQL_CALC_FOUND_ROWS created,str FROM (
            (SELECT int_id,created,str FROM `log` WHERE `address` = ?)
            UNION ALL
            (SELECT int_id,created,str FROM `message` WHERE `str` REGEXP ?)
            ) AS ut
            ORDER BY int_id ASC, created ASC
            LIMIT 100", { Slice => {} }, $search, '\b' . $search . '\b');

        if (@$data) {
            if (@$data == 100) {
                ($total) = $dbh->selectrow_array("SELECT FOUND_ROWS()");

                if ($total > 100) {
                    $message = "<div style='padding: 10px 0;'><b>Выводится 100 из $total</b></div>";
                }
            }

            $result = "<table style='margin-top:10px;' border=1 cellpadding=2 cellspacing=0>";

            foreach (@$data) {
                $result .= "<tr><td>" . $_->{created} . "</td><td>" . $_->{str} . "</td></tr>";
            }
            $result .= "</table>";
        }
        else {
            $message = "<div style='padding: 10px 0;'><b>Ничего не найдено</b></div>";
        }
    }

    $search =~ s/"/&quot;/g;

    print "Content-Type: text/html; charset=utf-8\n\n";

    print <<HTML;
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Поиск по адресу</title>
  </head>
  <body>
  <form method="get">
    <input type="text" required name="search" value="$search">
    <button type="submit">Искать</button>
    <button type="button" onclick="document.getElementsByName('search')[0].value='';">Очистить</button>
</form>
$message
$result
  </body>
</html>
HTML
}