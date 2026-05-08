import React from "react";
import JitsiWidget from "../../../components/JitsiWidget";

type Props = {
  params: { room: string };
};

export default function Page({ params }: Props) {
  const room = params?.room || "graftai-default-room";

  return (
    <div style={{ width: "100%", height: "100vh" }}>
      <JitsiWidget roomName={room} displayName="Guest" />
    </div>
  );
}
