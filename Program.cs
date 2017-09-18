using Microsoft.Extensions.CommandLineUtils;
using Newtonsoft.Json.Linq;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;

namespace ZfsAzureKeyvault
{
  class Program
  {
    static async Task<int> Main(string[] args)
    {
      int retval = 0;

      // FIXME https://github.com/aspnet/Common/commit/2230370a3985fd1bbeebbdd904a3dd348f612d35
      var app = new CommandLineApplication();
      CommandOption prefix = app.Option("--prefix", "Name prefix for all Key Vault secrets", CommandOptionType.SingleValue);
      CommandOption clientId = app.Option("--clientId", "AAD Application ID", CommandOptionType.SingleValue);
      CommandOption tenant = app.Option("--tenant", "AAD tenant name or ID", CommandOptionType.SingleValue);
      CommandOption kv_uri = app.Option("--keyvault-uri", "Azure Key Vault URI (https://YOUR_KVNAME.vault.azure.net)", CommandOptionType.SingleValue);
      CommandOption method = app.Option("--method", "stdin or tmpfile", CommandOptionType.SingleValue);
      CommandArgument filesystems = app.Argument("filesystems", "One or more filesystem names", multipleValues: true);
      app.HelpOption("-? | -h | --help");
      app.Execute(args);

      if (!clientId.HasValue() || !tenant.HasValue() || !method.HasValue() || !prefix.HasValue() || !kv_uri.HasValue()) {
        Console.Error.WriteLine("One or more required parameters are missing.");
        app.ShowHelp();
        return 1;
      }

      var validMethods = new List<string> { "stdin", "tmpfile" };
      if (!validMethods.Contains(method.Value())) {
        Console.Error.WriteLine($"Invalid method '{method}'.");
        app.ShowHelp();
        return 1;
      }

      if (filesystems.Values.Count == 0) {
        Console.Error.WriteLine("No filesystems were supplied.");
        app.ShowHelp();
        return 1;
      }

      IZfsKeyLoader provider;
      switch (method.Value()) {
        case "stdin":
          provider = new StdinZfsKeyLoader();
          break;
        case "tmpfile":
          provider = new TmpfileZfsKeyLoader();
          break;
        default:
          return 1;
      }

      var authHelper = new AuthHelper(tenant.Value(), clientId.Value());
      var token = authHelper.GetToken();

      foreach (string filesystem in filesystems.Values)
      {
        var client = new HttpClient();
        client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token.AccessToken);

        string response = "";
        try
        {
          // Replace '/' and '_' for '-' and remove any other non-alphanumeric chars
          Regex rgx = new Regex("[^a-zA-Z0-9-]");
          var santiziedFilesystem = rgx.Replace(filesystem.Replace('/', '-').Replace('_', '-'), "");
          var url = $"{kv_uri.Value()}/secrets/{prefix.Value()}-zfs-{santiziedFilesystem}/?api-version=2016-10-01";
          response = await client.GetStringAsync(url);
        }
        catch (HttpRequestException ex)
        {
          Console.WriteLine($"Error: failed to obtain secret for {filesystem} from Key Vault over HTTP: {ex.Message}");
          continue;
        }

        var passphrase = "";
        try
        {
          JObject json = JObject.Parse(response);
          passphrase = json["value"].ToString();
        }
        catch (Exception ex)
        {
          Console.WriteLine($"Error: failed to parse secret from Key Vault response for {filesystem}");
        }

        try {
          await provider.LoadKey(filesystem, passphrase);
        }
        catch (Exception ex) {
          retval = 1;
          Console.WriteLine($"Error: failed to load key for {filesystem}");
        }
      }

      return retval;
    }
  }
}
