using System;
using System.Diagnostics;
using System.Threading;
using System.Threading.Tasks;

namespace ZfsAzureKeyvault
{
  class TmpfileZfsKeyLoader : IZfsKeyLoader
  {
    public async Task LoadKey(string filesystem, string passphrase)
    {
      var process = new Process();
      process.StartInfo = new ProcessStartInfo
      {
        FileName = "zfs",
        Arguments = $"load-key {filesystem}",
      };

      var cts = new CancellationTokenSource(5000);
      var task = Utils.RunProcessAsync(process, cts.Token);
      Thread.Sleep(1000);
      process.StandardInput.Write(passphrase + "\n");

      int returnCode = await task;
      if (returnCode == 0)
      {
        Console.WriteLine($"Loaded key for {filesystem}.");
      }
      else
      {
        Console.WriteLine($"Warning: load-key operation for {filesystem} failed with non-zero status {returnCode}.");
      }
    }
  }
}