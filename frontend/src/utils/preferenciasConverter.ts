export const convertPreferenciasToDict = (preferencias?: Array<{categoria: string; texto: string}>) => {
  if (!preferencias) return undefined;
  
  return preferencias.reduce((acc, item) => {
    acc[item.categoria] = item.texto.split(',');
    return acc;
  }, {} as Record<string, string[]>);
};