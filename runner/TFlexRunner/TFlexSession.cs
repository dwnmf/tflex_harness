using TFlex;

namespace TFlexRunner
{
    internal static class TFlexSession
    {
        public static ApplicationSessionSetup CreateReadOnlySetup(bool enable3D)
        {
            var setup = new ApplicationSessionSetup();
            setup.ReadOnly = true;
            setup.Enable3D = enable3D;
            setup.EnableDOCs = false;
            setup.EnableMacros = false;
            setup.PromptToSaveModifiedDocuments = false;
            setup.ProtectionLicense = ApplicationSessionSetup.License.TFlexAPI;
            return setup;
        }

        public static bool IsInitialized
        {
            get { return Application.IsSessionInitialized; }
        }
    }
}
