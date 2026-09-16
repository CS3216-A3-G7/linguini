export type SceneArtId = "street" | "cafe" | "market" | "bedroom" | "kitchen" | "park";

type Props = {
  scene: SceneArtId;
  className?: string;
};

const sky = "#cfe8ef";
const ground = "#e8ddc7";
const leaf = "#9ac6a4";
const wood = "#c98f5b";
const brick = "#f0d9b5";

function Street() {
  return (
    <>
      <rect width="320" height="200" fill={sky} />
      <rect y="132" width="320" height="68" fill="#b9b2a4" />
      <rect y="126" width="320" height="8" fill={ground} />
      <rect x="10" y="40" width="70" height="90" rx="6" fill={brick} stroke="#21716f" strokeWidth="2" />
      <rect x="22" y="54" width="18" height="20" rx="3" fill="#fff9ed" />
      <rect x="50" y="54" width="18" height="20" rx="3" fill="#fff9ed" />
      <rect x="22" y="86" width="18" height="20" rx="3" fill="#fff9ed" />
      <rect x="50" y="86" width="18" height="20" rx="3" fill="#fff9ed" />
      <rect x="92" y="60" width="58" height="70" rx="6" fill="#f6c9ad" stroke="#21716f" strokeWidth="2" />
      <rect x="104" y="74" width="34" height="24" rx="3" fill="#fff9ed" />
      <rect x="190" y="72" width="92" height="52" rx="10" fill="#f9b233" stroke="#21716f" strokeWidth="2" />
      <rect x="200" y="82" width="26" height="20" rx="4" fill="#cfe8ef" />
      <rect x="234" y="82" width="26" height="20" rx="4" fill="#cfe8ef" />
      <circle cx="210" cy="126" r="9" fill="#263238" />
      <circle cx="264" cy="126" r="9" fill="#263238" />
      <rect x="162" y="96" width="8" height="34" fill={wood} />
      <circle cx="166" cy="82" r="22" fill={leaf} />
      <circle cx="150" cy="92" r="14" fill={leaf} />
      <circle cx="182" cy="92" r="14" fill={leaf} />
      <rect x="292" y="84" width="6" height="46" fill="#667579" />
      <rect x="286" y="62" width="18" height="26" rx="6" fill="#2e9c99" />
    </>
  );
}

function Cafe() {
  return (
    <>
      <rect width="320" height="200" fill="#f6e6cd" />
      <rect y="140" width="320" height="60" fill={ground} />
      <rect x="0" y="0" width="320" height="26" fill="#e85d32" />
      <rect x="30" y="34" width="120" height="96" rx="8" fill="#fff9ed" stroke="#21716f" strokeWidth="2" />
      <rect x="44" y="50" width="92" height="46" rx="4" fill="#cfe8ef" />
      <rect x="180" y="96" width="110" height="10" rx="5" fill={wood} />
      <rect x="228" y="106" width="8" height="40" fill={wood} />
      <rect x="208" y="144" width="48" height="8" rx="4" fill={wood} />
      <path d="M196 74h30a6 6 0 0 1 6 6v12a12 12 0 0 1-12 12h-18a6 6 0 0 1-6-6V80a6 6 0 0 1 6-6z" fill="#fff9ed" stroke="#21716f" strokeWidth="2" />
      <path d="M232 80h8a8 8 0 0 1 0 16h-8" fill="none" stroke="#21716f" strokeWidth="2" />
      <rect x="258" y="70" width="22" height="34" rx="4" fill="#dcebdd" stroke="#21716f" strokeWidth="2" />
      <circle cx="80" cy="150" r="14" fill="#f9b233" />
      <rect x="66" y="150" width="28" height="18" rx="6" fill="#f9b233" />
    </>
  );
}

function Market() {
  return (
    <>
      <rect width="320" height="200" fill="#fff1d2" />
      <rect y="150" width="320" height="50" fill={ground} />
      <path d="M20 40h280l-16 28H36z" fill="#e85d32" />
      <rect x="36" y="68" width="248" height="10" fill="#c94e2c" />
      <rect x="40" y="96" width="72" height="54" rx="8" fill={wood} stroke="#21716f" strokeWidth="2" />
      <circle cx="58" cy="108" r="9" fill="#e85d32" />
      <circle cx="78" cy="106" r="9" fill="#e85d32" />
      <circle cx="98" cy="110" r="9" fill="#e85d32" />
      <rect x="126" y="96" width="72" height="54" rx="8" fill={wood} stroke="#21716f" strokeWidth="2" />
      <circle cx="144" cy="108" r="9" fill="#f9b233" />
      <circle cx="164" cy="106" r="9" fill="#f9b233" />
      <circle cx="184" cy="110" r="9" fill="#f9b233" />
      <rect x="212" y="96" width="72" height="54" rx="8" fill={wood} stroke="#21716f" strokeWidth="2" />
      <ellipse cx="232" cy="110" rx="11" ry="8" fill={leaf} />
      <ellipse cx="258" cy="108" rx="11" ry="8" fill={leaf} />
      <ellipse cx="274" cy="116" rx="9" ry="7" fill={leaf} />
    </>
  );
}

function Bedroom() {
  return (
    <>
      <rect width="320" height="200" fill="#f3ecdf" />
      <rect y="146" width="320" height="54" fill={wood} opacity="0.5" />
      <rect x="28" y="86" width="150" height="60" rx="10" fill="#fff9ed" stroke="#21716f" strokeWidth="2" />
      <rect x="40" y="96" width="50" height="26" rx="8" fill="#cfe8ef" />
      <rect x="96" y="96" width="70" height="46" rx="8" fill="#e85d32" opacity="0.7" />
      <rect x="200" y="60" width="86" height="86" rx="8" fill={wood} stroke="#21716f" strokeWidth="2" />
      <rect x="210" y="72" width="66" height="8" rx="4" fill="#fff9ed" />
      <rect x="210" y="92" width="66" height="8" rx="4" fill="#fff9ed" />
      <rect x="210" y="112" width="40" height="8" rx="4" fill="#fff9ed" />
      <rect x="60" y="24" width="70" height="46" rx="6" fill="#cfe8ef" stroke="#21716f" strokeWidth="2" />
      <circle cx="196" cy="40" r="16" fill="#f9b233" />
    </>
  );
}

function Kitchen() {
  return (
    <>
      <rect width="320" height="200" fill="#eef3ec" />
      <rect y="130" width="320" height="70" fill="#dcebdd" />
      <rect x="0" y="120" width="320" height="14" fill={wood} />
      <rect x="24" y="40" width="80" height="54" rx="6" fill="#fff9ed" stroke="#21716f" strokeWidth="2" />
      <rect x="130" y="34" width="60" height="86" rx="8" fill="#cfd8dc" stroke="#21716f" strokeWidth="2" />
      <rect x="140" y="52" width="12" height="20" rx="4" fill="#667579" />
      <path d="M224 66h34a6 6 0 0 1 6 6v14a14 14 0 0 1-14 14h-18a14 14 0 0 1-14-14V72a6 6 0 0 1 6-6z" fill="#fff9ed" stroke="#21716f" strokeWidth="2" />
      <rect x="216" y="58" width="54" height="8" rx="4" fill="#e85d32" />
      <circle cx="60" cy="150" r="16" fill="#fff9ed" stroke="#21716f" strokeWidth="2" />
      <circle cx="100" cy="154" r="12" fill="#f9b233" />
      <rect x="150" y="142" width="46" height="26" rx="6" fill="#e85d32" opacity="0.8" />
    </>
  );
}

function Park() {
  return (
    <>
      <rect width="320" height="200" fill={sky} />
      <rect y="120" width="320" height="80" fill="#bcd9a8" />
      <path d="M0 126c60-16 110 10 170-2s110-12 150 4v-10H0z" fill="#a7cd90" />
      <rect x="44" y="86" width="10" height="44" fill={wood} />
      <circle cx="49" cy="70" r="28" fill={leaf} />
      <circle cx="26" cy="84" r="18" fill={leaf} />
      <circle cx="72" cy="84" r="18" fill={leaf} />
      <rect x="150" y="112" width="70" height="8" rx="4" fill={wood} />
      <rect x="150" y="96" width="70" height="8" rx="4" fill={wood} />
      <rect x="154" y="120" width="6" height="18" fill="#667579" />
      <rect x="210" y="120" width="6" height="18" fill="#667579" />
      <circle cx="270" cy="146" r="14" fill="#fff9ed" stroke="#21716f" strokeWidth="2" />
      <circle cx="272" cy="40" r="20" fill="#f9b233" />
    </>
  );
}

const scenes: Record<SceneArtId, () => React.JSX.Element> = {
  street: Street,
  cafe: Cafe,
  market: Market,
  bedroom: Bedroom,
  kitchen: Kitchen,
  park: Park,
};

export function SceneArt({ scene, className }: Props) {
  const Art = scenes[scene];
  return (
    <svg className={className} viewBox="0 0 320 200" preserveAspectRatio="xMidYMid slice" role="presentation">
      <Art />
    </svg>
  );
}
