export async function blobToText(data: Blob | string): Promise<string> {
  if (typeof data === 'string') return data;
  return data.text();
}