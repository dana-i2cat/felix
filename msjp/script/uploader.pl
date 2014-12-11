#!/usr/bin/perl -w
END{ &disconnect() }
use strict;
use DBI;
use Getopt::Long;
use Data::Dumper;
my %opts = ();
GetOptions(\%opts,'metakey=s', 'dsn=s', 'user=s', 'passwd=s', 'help');
my $dbh;
my $val;
my $meta;
my $retry_count = 3;

sub help()
{
	my $basename = ($0 =~ /(^|\/)([^\/]+$)/)[1];
print STDERR <<USG;
Usage: $basename [-h] -m METAKEYS -d DSN [-u USER] [-p PASSWD]
Upload comma separated data from STDIN to specified database. 

	-m, --metakey=METAKEYS         comma separated metaData keywords 
	-d, --dsn=DSN                  Data Source Name
	-u, --user=USER                DB username
	-p, --passwd=PASSWD            DB password
	-h, --help                     display this help and exit 

i.e. Executing the command below is equivalent with executing the following SQL.

 \$ echo 'timestamp,1249019917,sender,host1,reciever,host2,bandwidth,89.5' | $basename -m 'sender,reciever' -d "dbi:mysql:some_table:localhost"

 mysql> insert into data_200907(bandwidth,timestamp) values('89.5','1249019917')

USG
	exit 1;
}

sub main() {
	&help() if $opts{help} or !($opts{dsn} && $opts{metakey});
	$dbh = DBI->connect($opts{dsn}, $opts{user}||'root', $opts{passwd}||'', {RaiseError=>1});
	my $stdinval=<>;
	chomp($stdinval);
	$val = {split(',', $stdinval)};
if (!$val){
	print STDERR "No Data in uploader.pl.";
	return -1;
}
	map {$meta->{$_}=$val->{$_} if $val->{$_} ;delete $val->{$_}} split ',', $opts{metakey};
 if ( defined($val->{timestamp}) ) {
	my $table = "data_". (sprintf('%4d%02d', (gmtime($val->{timestamp}))[5,4]) + 190001);
	$dbh->prepare("create table $table like data")->execute() 
		unless $dbh->selectrow_arrayref("show tables like '$table'");
	if(my $metaId = &getMetaId())
	{
		my $query = sprintf('insert into %s(metaId, %s) values(%s,%s)', 
				$table,
				join(',', keys %{$val}),
				$metaId,
				join(',', map { "'".$val->{$_}."'" }keys %{$val}) 
		);
		print($query);
		eval {$dbh->prepare($query)->execute();};
		if ($@) {
			print STDERR $dbh->errstr;
		}
	}
	else
	{
		print STDERR "Failed to execute query";
	}
 } else {
        print STDERR "timestamp is null ";
        return -1;
 }
}
sub disconnect()
{
	$dbh->disconnect() if $dbh;
}
sub getMetaId()
{
	my $where = join(' and ', map { sprintf("%s = '%s'", $_, $meta->{$_}) }keys %{$meta}); 
	my $res = $dbh->selectrow_arrayref("select metaID from metaData where $where") if $where;

	my $metaId = $res->[0] if $res;
	if(!$metaId && $retry_count--)
	{
		my $query = sprintf('insert into metaData(%s) values(%s)',
				join(',', keys %{$meta}),
				join(',', map { "'".$meta->{$_}."'" }keys %{$meta})
		);
		print($query.'\n');
		$metaId = &getMetaId() if($dbh->prepare($query)->execute());		
	}
	$metaId;
}
&main();
1;

