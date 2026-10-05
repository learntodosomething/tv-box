# TV Box - a python-ra vonatkozo bejovo TILTO (Block) tuzfalszabalyok listazasa es torlese.
# A Windows ilyet akkor hoz letre, ha a "Windows biztonsagi riasztas" ablakot lezarod / megszakitod.
# A tiltó szabaly felulirja az engedelyezot, ezert a telefon akkor sem er el semmit.
$rules = Get-NetFirewallRule -Direction Inbound -Action Block -ErrorAction SilentlyContinue
$hits = @()
foreach ($r in $rules) {
  $app = ($r | Get-NetFirewallApplicationFilter).Program
  if ($app -and $app -like '*python*') {
    $hits += [pscustomobject]@{ Name = $r.Name; Rule = $r.DisplayName; Enabled = $r.Enabled; Profile = $r.Profile; Program = $app }
  }
}
if ($hits.Count -eq 0) {
  Write-Host 'Nincs python-ra vonatkozo tilto (Block) szabaly - ez nem az ok.'
  exit
}
Write-Host 'Talalt tilto szabalyok:'
$hits | Format-Table Rule, Enabled, Profile, Program -AutoSize | Out-String | Write-Host
$ans = Read-Host 'Torlom ezeket a szabalyokat? (i/n)'
if ($ans -eq 'i') {
  foreach ($h in $hits) { Remove-NetFirewallRule -Name $h.Name; Write-Host ('Torolve: ' + $h.Rule + ' ' + $h.Program) }
  Write-Host ''
  Write-Host 'Kesz. Inditsd ujra a TV Box-ot; ha a Windows rakerdez, valaszd: Engedelyezes (Private halozat).'
} else {
  Write-Host 'Nem torolt semmit.'
}
