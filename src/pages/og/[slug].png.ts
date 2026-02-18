import type { APIRoute, GetStaticPaths } from "astro";
import { getCollection } from "astro:content";
import { renderPng, loadImageAsDataUrl } from "../../lib/og";

export const getStaticPaths: GetStaticPaths = async () => {
  const songs = await getCollection("songs");
  return songs.map((song) => ({
    params: { slug: song.id },
    props: { song },
  }));
};

export const GET: APIRoute = async ({ props }) => {
  const { song } = props as { song: Awaited<ReturnType<typeof getCollection>>[number] };

  const coverDataUrl = song.data.coverArt
    ? loadImageAsDataUrl(song.data.coverArt)
    : null;

  const featuredLyrics = song.data.featuredLyrics;

  const element = {
    type: "div",
    props: {
      style: {
        display: "flex",
        width: "100%",
        height: "100%",
        backgroundColor: "#020303",
      },
      children: [
        // Album art - fills left side
        coverDataUrl
          ? {
              type: "img",
              props: {
                src: coverDataUrl,
                width: 630,
                height: 630,
                style: { objectFit: "cover" as const },
              },
            }
          : {
              type: "div",
              props: {
                style: {
                  width: "630px",
                  height: "630px",
                  backgroundColor: "#0e1010",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "120px",
                  color: "#f4ba0b",
                  flexShrink: 0,
                },
                children: "\u266B",
              },
            },
        // Text content - right side
        {
          type: "div",
          props: {
            style: {
              display: "flex",
              flexDirection: "column",
              justifyContent: "center",
              padding: "48px",
              flex: 1,
              gap: "16px",
            },
            children: [
              // Band name
              {
                type: "div",
                props: {
                  style: {
                    fontSize: "16px",
                    fontWeight: 700,
                    color: "#f4ba0b",
                    letterSpacing: "0.16em",
                    textTransform: "uppercase" as const,
                  },
                  children: "Real Don Music",
                },
              },
              // Song title
              {
                type: "div",
                props: {
                  style: {
                    fontSize: "52px",
                    fontWeight: 700,
                    color: "#ffffff",
                    lineHeight: 1.15,
                  },
                  children: song.data.title,
                },
              },
              // Album name
              ...(song.data.album
                ? [
                    {
                      type: "div",
                      props: {
                        style: {
                          fontSize: "22px",
                          fontWeight: 400,
                          color: "#888888",
                          marginTop: "8px",
                        },
                        children: song.data.album,
                      },
                    },
                  ]
                : []),
              // Featured lyrics if available
              ...(featuredLyrics
                ? [
                    {
                      type: "div",
                      props: {
                        style: {
                          fontSize: "18px",
                          fontWeight: 400,
                          color: "#888888",
                          marginTop: "16px",
                          fontStyle: "italic" as const,
                          lineHeight: 1.5,
                        },
                        children: `\u201C${featuredLyrics}\u201D`,
                      },
                    },
                  ]
                : []),
            ],
          },
        },
      ],
    },
  };

  const png = await renderPng(element, 1200, 630);
  return new Response(png, {
    headers: { "Content-Type": "image/png" },
  });
};
