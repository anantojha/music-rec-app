import "@/components/Waveform.css";

interface WaveformProps {
  label?: string;
  size?: "sm" | "md" | "lg";
}

const BAR_HEIGHTS = [0.4, 0.75, 1, 0.55, 0.85, 0.35, 0.65, 0.9, 0.5, 0.7];

/**
 * The page's signature element: an equalizer-style waveform, used wherever the
 * app is "listening" or "thinking" -- initial auth check, playlist analysis,
 * and the GPT ranking step. Echoes the console/VU-meter design language instead
 * of a generic spinner.
 */
export function Waveform({ label, size = "md" }: WaveformProps) {
  return (
    <div className={`waveform waveform-${size}`} role="status" aria-live="polite">
      <div className="waveform-bars" aria-hidden="true">
        {BAR_HEIGHTS.map((height, index) => (
          <span
            key={index}
            className="waveform-bar"
            style={{ ["--bar-height" as string]: height, animationDelay: `${index * 0.08}s` }}
          />
        ))}
      </div>
      {label && <span className="waveform-label mono">{label}</span>}
    </div>
  );
}
