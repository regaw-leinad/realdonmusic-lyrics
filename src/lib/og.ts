import satori from "satori";
import { Resvg } from "@resvg/resvg-js";
import fs from "node:fs";
import path from "node:path";

let regularFont: ArrayBuffer | null = null;
let boldFont: ArrayBuffer | null = null;

function loadFonts(): { regular: ArrayBuffer; bold: ArrayBuffer } {
  if (!regularFont) {
    regularFont = fs.readFileSync(path.resolve("public/fonts/Inter-Regular.ttf")).buffer as ArrayBuffer;
  }
  if (!boldFont) {
    boldFont = fs.readFileSync(path.resolve("public/fonts/Inter-Bold.ttf")).buffer as ArrayBuffer;
  }
  return { regular: regularFont, bold: boldFont };
}

export async function renderPng(
  element: Parameters<typeof satori>[0],
  width: number,
  height: number,
): Promise<Buffer> {
  const { regular, bold } = loadFonts();

  const svg = await satori(element, {
    width,
    height,
    fonts: [
      { name: "Inter", data: regular, weight: 400, style: "normal" },
      { name: "Inter", data: bold, weight: 700, style: "normal" },
    ],
  });

  const scale = 2;
  const resvg = new Resvg(svg, {
    fitTo: { mode: "width", value: width * scale },
  });
  return Buffer.from(resvg.render().asPng());
}

export function loadImageAsDataUrl(imagePath: string): string | null {
  const fullPath = path.resolve("public", imagePath.replace(/^\//, ""));
  if (!fs.existsSync(fullPath)) return null;
  const data = fs.readFileSync(fullPath);
  const ext = path.extname(fullPath).slice(1);
  const mime = ext === "jpg" ? "image/jpeg" : `image/${ext}`;
  return `data:${mime};base64,${data.toString("base64")}`;
}
