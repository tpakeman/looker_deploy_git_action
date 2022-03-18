view: usa_1910_current {
  sql_table_name: `bigquery-public-data.usa_names.usa_1910_current`
    ;;

  dimension: gender {
    type: string
    case: {
      when: {sql: ${TABLE}.gender = 'M';; label:"Male"}
      else: "Female"
    }
  }

  dimension: name {
    type: string
    description: "Given name of a person at birth"
    sql: ${TABLE}.name ;;
  }

  dimension: name_first_letter {
    type: string
    label: "First Letter of Name"
    sql: LEFT(${name}, 1) ;;
  }

  dimension: name_starts_with_vowel {
    type: yesno
    sql: ${name_first_letter} IN ('A', 'E', 'I', 'O', 'U') ;;
  }

  dimension: number {
    type: number
    description: "Number of occurrences of the name"
    sql: ${TABLE}.number ;;
  }

  dimension: state {
    type: string
    description: "2-digit state code"
    sql: ${TABLE}.state ;;
  }

  dimension: year {
    type: number
    description: "4-digit year of birth"
    sql: ${TABLE}.year ;;
  }

  measure: count {
    type: count
    drill_fields: [name]
  }

  measure: count_female {
    type: count
    filters: [gender: "Female"]
  }

  measure: count_male {
    type: count
    filters: [gender: "Male"]
  }

  measure: percent_of_total_are_male {
    type: number
    value_format_name: percent_1
    sql: 1.0 * ${count_male} / NULLIF(${count}, 0) ;;
  }

  measure: percent_of_total_are_female {
    type: number
    value_format_name: percent_1
    sql: 1.0 * ${count_female} / NULLIF(${count}, 0) ;;
  }
}
