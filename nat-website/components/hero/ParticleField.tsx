"use client";

import { useEffect, useRef } from "react";

// NAT's own palette for the particle field — Dala's reference used violet/amber/magenta,
// but constitution Principle I requires NAT's teal/dark-gray brand instead.
const PARTICLE_COLORS = ["#22d3ee", "#0891b2", "#67e8f9", "#94a3b8", "#e2e8f0"];

type Particle = {
  homeX: number;
  homeY: number;
  x: number;
  y: number;
  size: number;
  color: string;
  rotation: number;
  phase: number;
  speed: number;
  drift: number;
};

/**
 * Signature hero visual: an animated cloud of tiny triangles forming an organic,
 * brain-like silhouette (structurally carried over from the Dala reference — see
 * brand-assets/design/DESIGN-reference-dala.md — re-colored to NAT's own palette).
 * Ambient idle drift always runs; mouse proximity adds a local repulsion offset on
 * pointer-capable devices. Renders one static frame under prefers-reduced-motion.
 */
export default function ParticleField() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return; // No Canvas support — hero simply keeps its background color.

    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);

    let width = 0;
    let height = 0;
    let particles: Particle[] = [];
    let pointer: { x: number; y: number } | null = null;
    let rafId = 0;

    // Membership test for an organic, brain-like blob: a wide ellipse whose radius is
    // perturbed by a couple of sine harmonics (irregular lobed edge) plus a soft vertical
    // "cleft" that reads as two hemispheres without needing literal anatomy.
    function insideBrain(nx: number, ny: number): boolean {
      // nx, ny in [-1, 1] relative to the field's bounding box.
      const angle = Math.atan2(ny, nx);
      const dist = Math.sqrt(nx * nx + ny * ny);
      const wobble =
        1 +
        0.16 * Math.sin(angle * 3 + 0.6) +
        0.08 * Math.sin(angle * 7 - 1.2) +
        0.05 * Math.sin(angle * 11 + 2.1);
      const cleft = 0.06 * Math.exp(-Math.pow(nx * 4, 2)); // subtle waist at center
      const radius = 0.78 * wobble - cleft;
      return dist < radius;
    }

    function seedParticles() {
      particles = [];
      const targetCount = Math.round((width * height) / 2600); // density scales with area
      const denseCount = Math.min(Math.max(targetCount, 260), 700);
      let attempts = 0;
      while (particles.length < denseCount && attempts < denseCount * 20) {
        attempts++;
        const nx = Math.random() * 2 - 1;
        const ny = Math.random() * 2 - 1;
        if (!insideBrain(nx, ny)) continue;
        const x = width / 2 + nx * (width * 0.46);
        const y = height / 2 + ny * (height * 0.46);
        particles.push(makeParticle(x, y, 1.2 + Math.random() * 2.2));
      }
      // Sparse ambient field outside the main shape (lower density, per Dala's imagery notes).
      const ambientCount = Math.round(denseCount * 0.22);
      for (let i = 0; i < ambientCount; i++) {
        const x = Math.random() * width;
        const y = Math.random() * height;
        particles.push(makeParticle(x, y, 0.8 + Math.random() * 1.4));
      }
    }

    function makeParticle(x: number, y: number, size: number): Particle {
      return {
        homeX: x,
        homeY: y,
        x,
        y,
        size,
        color: PARTICLE_COLORS[Math.floor(Math.random() * PARTICLE_COLORS.length)],
        rotation: Math.random() * Math.PI * 2,
        phase: Math.random() * Math.PI * 2,
        speed: 0.4 + Math.random() * 0.5,
        drift: 6 + Math.random() * 10,
      };
    }

    function resize() {
      const rect = canvas!.getBoundingClientRect();
      width = rect.width;
      height = rect.height;
      canvas!.width = width * dpr;
      canvas!.height = height * dpr;
      ctx!.setTransform(dpr, 0, 0, dpr, 0, 0);
      seedParticles();
    }

    function drawTriangle(p: Particle) {
      const s = p.size * 3;
      ctx!.save();
      ctx!.translate(p.x, p.y);
      ctx!.rotate(p.rotation);
      ctx!.strokeStyle = p.color;
      ctx!.lineWidth = 1;
      ctx!.globalAlpha = 0.75;
      ctx!.beginPath();
      ctx!.moveTo(0, -s);
      ctx!.lineTo(s * 0.87, s * 0.5);
      ctx!.lineTo(-s * 0.87, s * 0.5);
      ctx!.closePath();
      ctx!.stroke();
      ctx!.restore();
    }

    function renderStatic() {
      ctx!.clearRect(0, 0, width, height);
      for (const p of particles) drawTriangle(p);
    }

    let t = 0;
    function tick() {
      t += 1;
      ctx!.clearRect(0, 0, width, height);
      for (const p of particles) {
        const idleX = Math.sin(t * 0.01 * p.speed + p.phase) * p.drift;
        const idleY = Math.cos(t * 0.013 * p.speed + p.phase) * p.drift;
        let targetX = p.homeX + idleX;
        let targetY = p.homeY + idleY;

        if (pointer) {
          const dx = targetX - pointer.x;
          const dy = targetY - pointer.y;
          const distSq = dx * dx + dy * dy;
          const radius = 140;
          if (distSq < radius * radius) {
            const dist = Math.sqrt(distSq) || 1;
            const force = (1 - dist / radius) * 26;
            targetX += (dx / dist) * force;
            targetY += (dy / dist) * force;
          }
        }

        p.x += (targetX - p.x) * 0.12;
        p.y += (targetY - p.y) * 0.12;
        p.rotation += 0.002 * p.speed;
        drawTriangle(p);
      }
      rafId = requestAnimationFrame(tick);
    }

    function handlePointerMove(event: PointerEvent) {
      const rect = canvas!.getBoundingClientRect();
      pointer = { x: event.clientX - rect.left, y: event.clientY - rect.top };
    }

    function handlePointerLeave() {
      pointer = null;
    }

    resize();
    window.addEventListener("resize", resize);

    if (reduceMotion) {
      renderStatic();
    } else {
      canvas.addEventListener("pointermove", handlePointerMove);
      canvas.addEventListener("pointerleave", handlePointerLeave);
      rafId = requestAnimationFrame(tick);
    }

    return () => {
      window.removeEventListener("resize", resize);
      canvas.removeEventListener("pointermove", handlePointerMove);
      canvas.removeEventListener("pointerleave", handlePointerLeave);
      if (rafId) cancelAnimationFrame(rafId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      className="absolute inset-0 h-full w-full"
    />
  );
}
