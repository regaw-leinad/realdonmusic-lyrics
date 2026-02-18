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

  // Album art on the left (square, not cropped), text centered on the right
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
        // Album art - square, fits height
        ...(coverDataUrl
          ? [
              {
                type: "img",
                props: {
                  src: coverDataUrl,
                  width: 630,
                  height: 630,
                  style: {
                    objectFit: "contain" as const,
                    flexShrink: 0,
                  },
                },
              },
            ]
          : [
              {
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
            ]),
        // Text content - right side, vertically centered
        {
          type: "div",
          props: {
            style: {
              display: "flex",
              flexDirection: "column",
              justifyContent: "center",
              padding: "48px 56px",
              flex: 1,
            },
            children: [
              // Band name
              {
                type: "div",
                props: {
                  style: {
                    fontSize: "20px",
                    fontWeight: 700,
                    color: "#f4ba0b",
                    letterSpacing: "0.14em",
                    textTransform: "uppercase" as const,
                    marginBottom: "20px",
                  },
                  children: "Real Don Music",
                },
              },
              // Song title
              {
                type: "div",
                props: {
                  style: {
                    fontSize: "56px",
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
                          marginTop: "20px",
                        },
                        children: song.data.album,
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
