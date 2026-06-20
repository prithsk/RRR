import * as ImageManipulator from 'expo-image-manipulator';

/**
 * Resize + compress a captured photo and return both a local URI and the
 * base64 payload (suitable for Google Vision / Claude). Resizing to ~1024px
 * keeps API costs and upload size down.
 */
export async function processPhoto(uri: string): Promise<{ uri: string; base64: string }> {
  const result = await ImageManipulator.manipulateAsync(
    uri,
    [{ resize: { width: 1024 } }],
    {
      compress: 0.7,
      format: ImageManipulator.SaveFormat.JPEG,
      base64: true,
    }
  );

  return {
    uri: result.uri,
    base64: result.base64 ?? '',
  };
}
