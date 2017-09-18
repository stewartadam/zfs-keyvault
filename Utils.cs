using System;
using System.Diagnostics;
using System.Threading;
using System.Threading.Tasks;

namespace ZfsAzureKeyvault
{
  class Utils
  {
    public static Task<int> RunProcessAsync(Process process, CancellationToken cancelToken)
    {
      var tcs = new TaskCompletionSource<int>();
      process.StartInfo.RedirectStandardInput = true;
      process.StartInfo.RedirectStandardOutput = true;
      process.StartInfo.RedirectStandardError = true;
      process.EnableRaisingEvents = true;

      // Have the Task return the process' exit code once available
      process.Exited += (sender, eventArgs) =>
      {
        tcs.SetResult(process.ExitCode);
      };

      // Kill the process upon cancellation
      cancelToken.Register(() =>
      {
        if (!process.HasExited)
        {
          Console.WriteLine($"Warning: killing process due to timeout.");
          process.Kill();
        }
      });

      bool started = process.Start();
      return tcs.Task;
    }
  }
}