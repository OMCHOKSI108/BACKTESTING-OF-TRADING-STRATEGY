export interface Source {
  url: string;
  text: string;
  title?: string;
  publish_date?: string;
}

export interface SearchQuery {
  query: string;
  sourceLinks: string[];
}

export enum OpenAIModel {
  DAVINCI_TURBO = "gpt-4o-mini",
}
