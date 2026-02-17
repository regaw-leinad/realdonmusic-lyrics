import { defineCollection } from "astro:content";
import { glob } from "astro/loaders";
import { z } from "astro/zod";

const songs = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/songs" }),
  schema: z.object({
    title: z.string(),
    coverArt: z.string().optional(),
    album: z.string().optional(),
    track: z.number().optional(),
    releaseDate: z.string().optional(),
    duration: z.string().optional(),
    writers: z.array(z.string()).optional(),
    spotifyUrl: z.string().url().optional(),
    appleMusicUrl: z.string().url().optional(),
    youtubeMusicUrl: z.string().url().optional(),
    bandcampUrl: z.string().url().optional(),
    description: z.string().optional(),
    featuredLyrics: z.string().optional(),
  }),
});

export const collections = { songs };
