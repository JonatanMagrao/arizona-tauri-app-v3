export default function TableRow({ id, type, loc, game, name, duration, owners, status }) {
  return (
    <tr>
      <td>{id}</td>
      <td>{type}</td>
      <td>{loc}</td>
      <td>{game}</td>
      <td>{name}</td>
      <td>{duration}</td>
      <td>{owners}</td>
      <td>{status}</td>
    </tr>

  )
}