using System;
using System.Linq;
using Microsoft.IdentityModel.Clients.ActiveDirectory;

/**
 * Some code in this class is based on the AAD deviceprofile sample:
 * https://github.com/Azure-Samples/active-directory-dotnet-deviceprofile/
 */
namespace ZfsAzureKeyvault {
  public class AuthHelper {
    public const string resource = "https://vault.azure.net";
    public string clientId = "";
    public string tenant = "";

    public AuthHelper(string tenant, string clientId) {
      this.tenant = tenant;
      this.clientId = clientId;
    }
    public AuthenticationResult GetToken()
    {
      AuthenticationContext ctx = null;
      if (tenant != null)
        ctx = new AuthenticationContext("https://login.microsoftonline.com/" + tenant);
      else
      {
        ctx = new AuthenticationContext("https://login.microsoftonline.com/common");
        if (ctx.TokenCache.Count > 0)
        {
          string homeTenant = ctx.TokenCache.ReadItems().First().TenantId;
          ctx = new AuthenticationContext("https://login.microsoftonline.com/" + homeTenant);
        }
      }
      AuthenticationResult result = null;
      try
      {
        result = ctx.AcquireTokenSilentAsync(resource, clientId).Result;
      }
      catch (Exception exc)
      {
        var adalEx = exc.InnerException as AdalException;
        if ((adalEx != null) && (adalEx.ErrorCode == "failed_to_acquire_token_silently"))
        {
          result = GetTokenViaCode(ctx);
        }
        else
        {
          Console.ForegroundColor = ConsoleColor.Red;
          Console.WriteLine("Something went wrong.");
          Console.WriteLine("Message: " + exc.InnerException.Message + "\n");
        }
      }
      return result;
    }
    public AuthenticationResult GetTokenViaCode(AuthenticationContext ctx)
    {
      AuthenticationResult result = null;
      try
      {
        DeviceCodeResult codeResult = ctx.AcquireDeviceCodeAsync(resource, clientId).Result;
        Console.ResetColor();
        Console.WriteLine("You need to sign in.");
        Console.WriteLine("Message: " + codeResult.Message + "\n");
        result = ctx.AcquireTokenByDeviceCodeAsync(codeResult).Result;
      }
      catch (Exception exc)
      {
        Console.ForegroundColor = ConsoleColor.Red;
        Console.WriteLine("Something went wrong.");
        Console.WriteLine("Message: " + exc.Message + "\n");
      }
      return result;
    }

    public void ClearCache()
    {
      AuthenticationContext ctx = new AuthenticationContext("https://login.microsoftonline.com/common");
      ctx.TokenCache.Clear();
      Console.ForegroundColor = ConsoleColor.Green;
      Console.WriteLine("Token cache cleared.");
    }

    public void PrintCache()
    {
      AuthenticationContext ctx = new AuthenticationContext("https://login.microsoftonline.com/common");
      var cacheContent = ctx.TokenCache.ReadItems();
      Console.ForegroundColor = ConsoleColor.Green;
      if (cacheContent.Count() > 0)
      {
        Console.WriteLine("{0,-30} | {1,-15}", "UPN", "TenantId");
        Console.WriteLine("-----------------------------------------------------------------");
        foreach (TokenCacheItem tci in cacheContent)
        {
          Console.WriteLine("{0,-30} | {1,-15}  ", tci.DisplayableId, tci.TenantId);
        }
        Console.WriteLine("-----------------------------------------------------------------");
      }
      else { Console.WriteLine("The cache is empty."); }
    }
  }
}