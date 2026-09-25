using System;
using System.Runtime.InteropServices;

namespace PhotoTailor;

internal static class WindowsFilePicker
{
	[StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
	private struct OpenFileName
	{
		public uint structSize;

		public IntPtr dialogOwner;

		public IntPtr instance;

		public IntPtr filter;

		public IntPtr customFilter;

		public uint maxCustomFilter;

		public uint filterIndex;

		public IntPtr file;

		public uint maxFile;

		public IntPtr fileTitle;

		public uint maxFileTitle;

		public IntPtr initialDirectory;

		public IntPtr title;

		public uint flags;

		public ushort fileOffset;

		public ushort fileExtension;

		public IntPtr defaultExtension;

		public IntPtr customData;

		public IntPtr hook;

		public IntPtr templateName;

		public IntPtr reservedPtr;

		public uint reservedInt;

		public uint flagsEx;
	}

	[DllImport("comdlg32.dll", CharSet = CharSet.Unicode, EntryPoint = "GetOpenFileNameW", SetLastError = true)]
	[return: MarshalAs(UnmanagedType.Bool)]
	private static extern bool GetOpenFileName(ref OpenFileName openFileName);

	[DllImport("comdlg32.dll")]
	private static extern uint CommDlgExtendedError();

	public static string? PickImage()
	{
		if (!OperatingSystem.IsWindows())
		{
			throw new PlatformNotSupportedException("当前原型的文件选择器暂只支持 Windows。");
		}
		IntPtr intPtr = IntPtr.Zero;
		IntPtr intPtr2 = IntPtr.Zero;
		IntPtr intPtr3 = IntPtr.Zero;
		IntPtr intPtr4 = IntPtr.Zero;
		try
		{
			intPtr = Marshal.StringToHGlobalUni("图片文件 (*.png;*.jpg;*.jpeg;*.webp;*.gif)\0*.png;*.jpg;*.jpeg;*.webp;*.gif\0所有文件 (*.*)\0*.*\0\0");
			intPtr2 = Marshal.AllocHGlobal(8192);
			for (int i = 0; i < 8192; i += 8)
			{
				Marshal.WriteInt64(intPtr2, i, 0L);
			}
			intPtr3 = Marshal.StringToHGlobalUni("选择要复刻的穿搭图片");
			intPtr4 = Marshal.StringToHGlobalUni("png");
			OpenFileName openFileName = new OpenFileName
			{
				structSize = (uint)Marshal.SizeOf<OpenFileName>(),
				filter = intPtr,
				filterIndex = 1u,
				file = intPtr2,
				maxFile = 4096u,
				title = intPtr3,
				defaultExtension = intPtr4,
				flags = 530440u
			};
			if (GetOpenFileName(ref openFileName))
			{
				return Marshal.PtrToStringUni(intPtr2);
			}
			uint num = CommDlgExtendedError();
			if (num == 0)
			{
				return null;
			}
			throw new InvalidOperationException($"Windows 图片选择窗口打开失败（错误码 0x{num:X4}）。");
		}
		finally
		{
			if (intPtr != IntPtr.Zero)
			{
				Marshal.FreeHGlobal(intPtr);
			}
			if (intPtr2 != IntPtr.Zero)
			{
				Marshal.FreeHGlobal(intPtr2);
			}
			if (intPtr3 != IntPtr.Zero)
			{
				Marshal.FreeHGlobal(intPtr3);
			}
			if (intPtr4 != IntPtr.Zero)
			{
				Marshal.FreeHGlobal(intPtr4);
			}
		}
	}
}
