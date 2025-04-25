
export const parseMarkdown = (text: string): string => {
  // Parse bold text
  let parsedText = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  
  // Parse italic text
  parsedText = parsedText.replace(/\*(.*?)\*/g, '<em>$1</em>');
  
  // Parse code
  parsedText = parsedText.replace(/`(.*?)`/g, '<code>$1</code>');
  
  // Parse links
  parsedText = parsedText.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-blue-500 underline">$1</a>');
  
  // Parse line breaks
  parsedText = parsedText.replace(/\n/g, '<br />');
  
  return parsedText;
};
