using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Microsoft.Win32;

namespace AuraSdkDiag
{
    class Program
    {
        static void print_bitness()
        {
            OutputMsg("64-bit OS: " + (System.Environment.Is64BitOperatingSystem ? "Yes" : "No"));
            OutputMsg("64-bit process: " + (System.Environment.Is64BitProcess ? "Yes" : "No"));
        }

        static void OutputError(string s)
        {
            Console.WriteLine("** [ERROR]: {0}", s);
        }

        static void OutputMsg(string s)
        {
            Console.WriteLine("{0}", s);
        }

        static void RetriveAuraInfo(RegistryKey rkClsid)
        {
            var rkSdk = rkClsid.OpenSubKey("{05921124-5057-483E-A037-E9497B523590}\\InprocServer32");
            if (rkSdk == null)
            {
                OutputError("Aura SDK not found in registry.");
                return;
            }
            OutputMsg("Aura SDK found!");
            string sdk_file = (string)rkSdk.GetValue("");
            OutputMsg("Location: " + sdk_file);
            var sdk_file_modified = System.IO.File.GetLastWriteTime(sdk_file);
            OutputMsg("Modified: " + sdk_file_modified.ToString());
            OutputMsg("Threading Model: " + rkSdk.GetValue("ThreadingModel"));
            OutputMsg("");

            var rkHalRoot = rkClsid.OpenSubKey("{9C9E903E-BBC7-4A0E-8326-ED6AC85B9FCC}\\Instance");
            var types = rkHalRoot.GetSubKeyNames();
            foreach (var type in types)
            {
                OutputMsg("HAL Type found: " + type);
                var rkHalType = rkHalRoot.OpenSubKey(type + "\\Instance");
                if (rkHalType != null)
                {
                    var hals = rkHalType.GetSubKeyNames();
                    foreach (var clsidHal in hals)
                    {
                        var rkHalEntry = rkHalType.OpenSubKey(clsidHal);
                        OutputMsg("--HAL: " + clsidHal);
                        OutputMsg("--Name: " + (string)rkHalEntry.GetValue("Name"));

                        // Try to open HAL in CLSID
                        var rkHal = rkClsid.OpenSubKey(clsidHal + "\\InprocServer32");
                        if (rkHal == null)
                        {
                            OutputError("HAL not found in CLSID!!");
                            continue;
                        }

                        string file_location = (string)rkHal.GetValue("");
                        OutputMsg("--Location: " + file_location);
                        var date_time = System.IO.File.GetLastWriteTime(file_location);
                        OutputMsg("--Modified: " + date_time.ToString());
                        OutputMsg("--ThreadingModel: " + (string)rkHal.GetValue("ThreadingModel"));
                        OutputMsg("");
                    }
                }
            }
        }

        static void Main(string[] args)
        {
            print_bitness();

            OutputMsg("======== " + (System.Environment.Is64BitProcess ? "64" : "32") + "-bit ========");
            var rkClsid = Registry.ClassesRoot.OpenSubKey("CLSID");
            for (int i = 0; i < 2; i++)
            {
                if (rkClsid == null)
                {
                    OutputError("CLSID not found. (!!)");
                }
                else
                {
                    RetriveAuraInfo(rkClsid);
                }

                if (!System.Environment.Is64BitProcess || i == 1)
                    break;

                OutputMsg("======== 32-bit ========");
                rkClsid = Registry.ClassesRoot.OpenSubKey("Wow6432Node\\CLSID");
            }
        }
    }
}
