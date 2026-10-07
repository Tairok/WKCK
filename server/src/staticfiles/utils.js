// Pobieranie ciasteczka po nazwie — potrzebne do CSRF
export function getCookie(name) {
    return document.cookie
        .split(";")
        .map(c => c.trim())
        .find(c => c.startsWith(name + "="))
        ?.split("=")[1] || "";
}

// Formatowanie bajtów na KB/MB/GB
export function bytes(v) {
  if (!v) return "n/a";
  const units = ["B", "KB", "MB", "GB"];
  let size = v, u = 0;

  while (size >= 1024 && u < units.length - 1) {
    size /= 1024;
    u++;
  }

  return `${size.toFixed(1)} ${units[u]}`;
}