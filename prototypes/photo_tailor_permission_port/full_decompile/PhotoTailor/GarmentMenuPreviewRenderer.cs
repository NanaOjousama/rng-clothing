using System;
using System.Collections.Generic;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;

namespace PhotoTailor;

internal static class GarmentMenuPreviewRenderer
{
	internal static void Populate(OutfitRenderPreview rendered, RecognitionPreviewResourceSet<Texture2D> resources, GraphicsDevice graphics)
	{
		//IL_0051: Unknown result type (might be due to invalid IL or missing references)
		//IL_0057: Expected O, but got Unknown
		//IL_00fe: Unknown result type (might be due to invalid IL or missing references)
		//IL_0105: Expected O, but got Unknown
		ArgumentNullException.ThrowIfNull(rendered, "rendered");
		ArgumentNullException.ThrowIfNull(resources, "resources");
		ArgumentNullException.ThrowIfNull(graphics, "graphics");
		Dictionary<string, Texture2D> dictionary = new Dictionary<string, Texture2D>(StringComparer.Ordinal);
		foreach (GarmentRenderPreview item in rendered.Items)
		{
			try
			{
				Texture2D val = new Texture2D(graphics, item.Width, item.Height);
				try
				{
					val.SetData<Color>(item.Pixels);
					resources.ReplacePart(item.ItemIndex, val);
				}
				catch
				{
					((GraphicsResource)val).Dispose();
					throw;
				}
			}
			catch (Exception error)
			{
				resources.ReportNonFatalFailure(item.Name + " 小图", error);
			}
			if (!item.HasArtwork)
			{
				continue;
			}
			try
			{
				string key = (string.IsNullOrWhiteSpace(item.LogicalGarmentId) ? $"item:{item.ItemIndex}" : item.LogicalGarmentId);
				if (!dictionary.TryGetValue(key, out var value))
				{
					value = new Texture2D(graphics, item.ArtworkWidth, item.ArtworkHeight);
					try
					{
						value.SetData<Color>(item.ArtworkPixels);
						dictionary[key] = value;
					}
					catch
					{
						((GraphicsResource)value).Dispose();
						throw;
					}
				}
				resources.ReplaceArtwork(item.ItemIndex, value);
			}
			catch (Exception error2)
			{
				resources.ReportNonFatalFailure(item.Name + " 高像素画稿", error2);
			}
		}
	}

	internal static GarmentMenuIconLayout GetLayout(string category, int textureWidth, int textureHeight)
	{
		//IL_003c: Unknown result type (might be due to invalid IL or missing references)
		//IL_004b: Unknown result type (might be due to invalid IL or missing references)
		//IL_007b: Unknown result type (might be due to invalid IL or missing references)
		//IL_008a: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ae: Unknown result type (might be due to invalid IL or missing references)
		//IL_00bd: Unknown result type (might be due to invalid IL or missing references)
		//IL_00e1: Unknown result type (might be due to invalid IL or missing references)
		//IL_00f0: Unknown result type (might be due to invalid IL or missing references)
		return category switch
		{
			"shirt" => new GarmentMenuIconLayout(new Rectangle(0, 0, Math.Min(8, textureWidth), Math.Min(8, textureHeight)), new Vector2(4f, 4f), 4f), 
			"pants" => new GarmentMenuIconLayout(new Rectangle(0, Math.Max(0, textureHeight - 16), Math.Min(16, textureWidth), Math.Min(16, textureHeight)), new Vector2(8f, 8f), 4f), 
			"hat" => new GarmentMenuIconLayout(new Rectangle(0, 0, Math.Min(20, textureWidth), Math.Min(20, textureHeight)), new Vector2(10f, 10f), 3f), 
			_ => new GarmentMenuIconLayout(new Rectangle(0, 0, Math.Min(16, textureWidth), Math.Min(16, textureHeight)), new Vector2(8f, 8f), 4f), 
		};
	}

	internal static void Draw(SpriteBatch batch, Texture2D texture, string category, Rectangle slot, float layerDepth = 0.9f)
	{
		//IL_0017: Unknown result type (might be due to invalid IL or missing references)
		//IL_0024: Unknown result type (might be due to invalid IL or missing references)
		//IL_0036: Unknown result type (might be due to invalid IL or missing references)
		//IL_0039: Unknown result type (might be due to invalid IL or missing references)
		//IL_0043: Unknown result type (might be due to invalid IL or missing references)
		//IL_004f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0072: Unknown result type (might be due to invalid IL or missing references)
		//IL_0077: Unknown result type (might be due to invalid IL or missing references)
		//IL_009c: Unknown result type (might be due to invalid IL or missing references)
		//IL_009d: Unknown result type (might be due to invalid IL or missing references)
		//IL_00a3: Unknown result type (might be due to invalid IL or missing references)
		//IL_00af: Unknown result type (might be due to invalid IL or missing references)
		GarmentMenuIconLayout layout = GetLayout(category, texture.Width, texture.Height);
		Vector2 val = default(Vector2);
		((Vector2)(ref val))._002Ector((float)((Rectangle)(ref slot)).Center.X, (float)((Rectangle)(ref slot)).Center.Y);
		batch.Draw(texture, val, (Rectangle?)layout.Source, Color.White, 0f, layout.Origin, layout.Scale, (SpriteEffects)0, layerDepth);
		if (category == "shirt")
		{
			Rectangle source = layout.Source;
			source.X += texture.Width / 2;
			if (((Rectangle)(ref source)).Right <= texture.Width)
			{
				batch.Draw(texture, val, (Rectangle?)source, Color.White, 0f, layout.Origin, layout.Scale, (SpriteEffects)0, Math.Min(0.9999999f, layerDepth + 1E-07f));
			}
		}
	}
}
