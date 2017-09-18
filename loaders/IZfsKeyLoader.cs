using System;
using System.Threading.Tasks;

namespace ZfsAzureKeyvault
{
  public interface IZfsKeyLoader
  {
    Task LoadKey(string filesystem, string passphrase);
  }
}