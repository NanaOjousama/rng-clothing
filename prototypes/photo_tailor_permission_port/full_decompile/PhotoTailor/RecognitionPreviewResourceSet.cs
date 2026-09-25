using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;

namespace PhotoTailor;

internal sealed class RecognitionPreviewResourceSet<TResource> : IDisposable where TResource : class, IDisposable
{
	private sealed class ReferenceComparer<T> : IEqualityComparer<T> where T : class
	{
		internal static readonly ReferenceComparer<T> Instance = new ReferenceComparer<T>();

		public bool Equals(T? left, T? right)
		{
			return left == right;
		}

		public int GetHashCode(T value)
		{
			return RuntimeHelpers.GetHashCode(value);
		}
	}

	private readonly int ownerThreadId = Environment.CurrentManagedThreadId;

	private readonly Dictionary<TResource, int> references = new Dictionary<TResource, int>(ReferenceComparer<TResource>.Instance);

	private readonly Dictionary<int, TResource> parts = new Dictionary<int, TResource>();

	private readonly Dictionary<int, TResource> artworks = new Dictionary<int, TResource>();

	private TResource? source;

	private bool disposed;

	private string? nonFatalWarning;

	internal TResource? Source => source;

	internal IReadOnlyDictionary<int, TResource> Parts => parts;

	internal IReadOnlyDictionary<int, TResource> Artworks => artworks;

	internal bool IsDisposed => disposed;

	internal bool IsOwnerThread => Environment.CurrentManagedThreadId == ownerThreadId;

	internal string? NonFatalWarning => nonFatalWarning;

	internal void ReplaceSource(TResource? resource)
	{
		EnsureMutable();
		if (source != resource)
		{
			TResource resource2 = source;
			AddReference(resource);
			source = resource;
			ReleaseReference(resource2);
		}
	}

	internal void ReplacePart(int itemIndex, TResource? resource)
	{
		EnsureMutable();
		if (itemIndex < 0)
		{
			throw new ArgumentOutOfRangeException("itemIndex");
		}
		parts.TryGetValue(itemIndex, out var value);
		if (value != resource)
		{
			AddReference(resource);
			if (resource == null)
			{
				parts.Remove(itemIndex);
			}
			else
			{
				parts[itemIndex] = resource;
			}
			ReleaseReference(value);
		}
	}

	internal void ReplaceArtwork(int itemIndex, TResource? resource)
	{
		EnsureMutable();
		if (itemIndex < 0)
		{
			throw new ArgumentOutOfRangeException("itemIndex");
		}
		artworks.TryGetValue(itemIndex, out var value);
		if (value != resource)
		{
			AddReference(resource);
			if (resource == null)
			{
				artworks.Remove(itemIndex);
			}
			else
			{
				artworks[itemIndex] = resource;
			}
			ReleaseReference(value);
		}
	}

	internal void ReportNonFatalFailure(string stage, Exception error)
	{
		EnsureMutable();
		string text = stage + "预览不可用：" + error.Message;
		if (string.IsNullOrWhiteSpace(nonFatalWarning))
		{
			nonFatalWarning = text;
		}
		else if (!nonFatalWarning.Contains(text, StringComparison.Ordinal))
		{
			nonFatalWarning = nonFatalWarning + "\n" + text;
		}
	}

	public void Dispose()
	{
		EnsureOwnerThread();
		if (disposed)
		{
			return;
		}
		disposed = true;
		source = null;
		parts.Clear();
		artworks.Clear();
		TResource[] array = references.Keys.ToArray();
		references.Clear();
		List<Exception> list = null;
		TResource[] array2 = array;
		foreach (TResource val in array2)
		{
			try
			{
				val.Dispose();
			}
			catch (Exception item)
			{
				if (list == null)
				{
					list = new List<Exception>();
				}
				list.Add(item);
			}
		}
		if (list == null)
		{
			return;
		}
		throw new AggregateException("一个或多个预览资源无法释放。", list);
	}

	private void AddReference(TResource? resource)
	{
		if (resource != null)
		{
			references.TryGetValue(resource, out var value);
			references[resource] = value + 1;
		}
	}

	private void ReleaseReference(TResource? resource)
	{
		if (resource != null && references.TryGetValue(resource, out var value))
		{
			if (value > 1)
			{
				references[resource] = value - 1;
				return;
			}
			references.Remove(resource);
			resource.Dispose();
		}
	}

	private void EnsureMutable()
	{
		EnsureOwnerThread();
		if (disposed)
		{
			throw new ObjectDisposedException("RecognitionPreviewResourceSet");
		}
	}

	private void EnsureOwnerThread()
	{
		if (!IsOwnerThread)
		{
			throw new InvalidOperationException("预览纹理必须在创建它们的游戏线程上修改或释放。");
		}
	}
}
