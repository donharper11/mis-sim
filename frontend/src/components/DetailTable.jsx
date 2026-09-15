/* eslint-disable react/prop-types */
export default function DetailTable({ columns, rows, onRowClick }) {
  return (
    <div className="detail-table-wrap">
      <table className="detail-table">
        <thead>
          <tr>{columns.map((column) => <th key={column.key} scope="col">{column.label}</th>)}<th scope="col"><span className="sr-only">Open</span></th></tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.key} className={onRowClick ? "detail-table__row--open" : ""} onClick={() => onRowClick?.(row)}>
              {columns.map((column, index) => <td key={column.key} className={index === 0 && onRowClick ? "detail-table__first-cell" : ""}>{row[column.key]}</td>)}
              <td className="detail-table__affordance">{onRowClick && <span aria-hidden="true">›</span>}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
