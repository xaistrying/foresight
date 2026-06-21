interface IconProps {
  size?: number;
  color?: string;
}

export default function ChatIcon({ size = 24, color = "currentColor" }: IconProps) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none">
      <path
        fill={color}
        d="M2 6a3 3 0 0 1 3-3h8a1 1 0 1 1 0 2H5a1 1 0 0 0-1 1v13l2.134-1.6a2 2 0 0 1 1.199-.4H19a1 1 0 0 0 1-1v-4a1 1 0 1 1 2 0v4a3 3 0 0 1-3 3H7.333L4 21.5c-.824.618-2 .03-2-1zm9 6a1 1 0 1 1 0 2H8a1 1 0 1 1 0-2zm4-4a1 1 0 1 1 0 2H8a1 1 0 1 1 0-2zm5-7a1 1 0 0 1 .946.677l.13.378c.3.879.99 1.57 1.87 1.87l.377.129a1 1 0 0 1 0 1.892l-.378.13c-.879.3-1.57.99-1.87 1.87l-.129.377a1 1 0 0 1-1.892 0l-.13-.378a3 3 0 0 0-1.87-1.87l-.377-.129a1 1 0 0 1 0-1.892l.378-.13c.879-.3 1.57-.99 1.87-1.87l.129-.377.062-.146A1 1 0 0 1 20 1m0 3.196a5 5 0 0 1-.804.804q.449.355.804.803.356-.447.803-.803A5 5 0 0 1 20 4.196"
      />
    </svg>
  );
}
