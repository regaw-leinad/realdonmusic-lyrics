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

  const children: any[] = [
    // Band name at top
    {
      type: "div",
      props: {
        style: {
          fontSize: "22px",
          fontWeight: 700,
          color: "#f4ba0b",
          letterSpacing: "0.16em",
          textTransform: "uppercase" as const,
          marginBottom: "36px",
        },
        children: "Real Don Music",
      },
    },
  ];

  // Album art - large
  if (coverDataUrl) {
    children.push({
      type: "img",
      props: {
        src: coverDataUrl,
        width: 860,
        height: 860,
        style: {
          borderRadius: "20px",
          objectFit: "cover" as const,
        },
      },
    });
  }

  // Song title
  children.push({
    type: "div",
    props: {
      style: {
        fontSize: "52px",
        fontWeight: 700,
        color: "#ffffff",
        textAlign: "center" as const,
        lineHeight: 1.2,
        marginTop: "36px",
      },
      children: song.data.title,
    },
  });

  // Album name
  if (song.data.album) {
    children.push({
      type: "div",
      props: {
        style: {
          fontSize: "26px",
          fontWeight: 400,
          color: "#888888",
          textAlign: "center" as const,
          marginTop: "10px",
        },
        children: song.data.album,
      },
    });
  }

  // Featured lyrics if available
  if (featuredLyrics) {
    children.push({
      type: "div",
      props: {
        style: {
          fontSize: "26px",
          fontWeight: 400,
          color: "#cccccc",
          textAlign: "center" as const,
          marginTop: "24px",
          fontStyle: "italic" as const,
          lineHeight: 1.5,
          maxWidth: "860px",
        },
        children: `\u201C${featuredLyrics}\u201D`,
      },
    });
  }

  // URL at bottom - pushed down with flex spacer
  children.push({
    type: "div",
    props: {
      style: { flex: 1 },
      children: "",
    },
  });

  children.push({
    type: "div",
    props: {
      style: {
        fontSize: "20px",
        fontWeight: 400,
        color: "#555555",
        letterSpacing: "0.04em",
      },
      children: "lyrics.realdonmusic.com",
    },
  });

  const element = {
    type: "div",
    props: {
      style: {
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        width: "100%",
        height: "100%",
        backgroundColor: "#020303",
        padding: "48px",
      },
      children,
    },
  };

  const png = await renderPng(element, 1080, 1350);
  return new Response(png, {
    headers: { "Content-Type": "image/png" },
  });
};
