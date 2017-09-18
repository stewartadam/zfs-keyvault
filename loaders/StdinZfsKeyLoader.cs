using System;
using System.Diagnostics;
using System.Threading;
using System.Threading.Tasks;

namespace ZfsAzureKeyvault
{
  class StdinZfsKeyLoader : IZfsKeyLoader
  {
    public async Task LoadKey(string filesystem, string secret)
    {
      var process = new Process();
      process.StartInfo = new ProcessStartInfo
      {
        FileName = "mktemp"
      };
      var cts = new CancellationTokenSource(5000);
      var task = Utils.RunProcessAsync(process, cts.Token);
      int returnCode = await task;
      if (returnCode != 0)
      {
        Console.WriteLine($"Error: Creating temporary key file for {filesystem} failed with non-zero status {returnCode}.");
        return;
      }

      var filename = process.StandardOutput.ReadLine();
      if (filename.Length == 0 || !System.IO.File.Exists(filename))
      {
        Console.WriteLine($"Error: Creating temporary key file for {filesystem} failed.");
        return;
      }

      var secretWriter = new System.IO.StreamWriter(filename);
      secretWriter.WriteLine(secret);
      secretWriter.Dispose();

      try
      {
        process = new Process();
        process.StartInfo = new ProcessStartInfo
        {
          FileName = "zfs",
          Arguments = $"load-key -L file://{filename} {filesystem}",
        };

        cts = new CancellationTokenSource(5000);
        returnCode = await Utils.RunProcessAsync(process, cts.Token);
        if (returnCode == 0)
        {
          Console.WriteLine($"Loaded key for {filesystem}.");
        }
        else
        {
          Console.WriteLine($"Warning: load-key operation for {filesystem} failed with non-zero status {returnCode}.");
        }
      }
      finally
      {
        System.IO.File.Delete(filename);
      }
    }
  }
}