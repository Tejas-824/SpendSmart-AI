export default function ModelBadge({ tier, cached }) {
  if (cached) {
    return <span className="badge badge--cached">cached</span>;
  }
  return (
    <span className={"badge " + (tier === "big" ? "badge--big" : "badge--small")}>
      {tier === "big" ? "big model" : "small model"}
    </span>
  );
}
