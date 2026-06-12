export type Result = {
  id: string; title: string; author: string; date: string;
  tradition: string[]; era: string; genre: string;
  tags: string[];
  citation: { source?: string; url?: string };
  snippet: string;
  score: number;
};
