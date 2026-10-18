/** Sample a [lon, lat] point at fraction t along a LineString. */
export function pointAtFraction(
  geometry: [number, number][],
  t: number,
): [number, number] {
  if (!geometry.length) return [0, 0]
  if (geometry.length === 1 || t <= 0) return geometry[0]
  if (t >= 1) return geometry[geometry.length - 1]

  const dists = [0]
  for (let i = 1; i < geometry.length; i++) {
    const [lon0, lat0] = geometry[i - 1]
    const [lon1, lat1] = geometry[i]
    const dlon = (lon1 - lon0) * Math.cos((((lat0 + lat1) / 2) * Math.PI) / 180)
    const dlat = lat1 - lat0
    dists.push(dists[i - 1] + Math.hypot(dlon, dlat))
  }
  const total = dists[dists.length - 1] || 1
  const target = t * total
  let i = 1
  while (i < dists.length && dists[i] < target) i++
  const a = geometry[i - 1]
  const b = geometry[Math.min(i, geometry.length - 1)]
  const seg = dists[i] - dists[i - 1] || 1
  const u = (target - dists[i - 1]) / seg
  return [a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u]
}
