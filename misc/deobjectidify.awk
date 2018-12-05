# --------------------------------------------------------------------------------
# deobjectidify.awk: Remove unwanted OBJECTID elements from INSERT INTO statements
# --------------------------------------------------------------------------------
# Usage: awk -f deobjectidify.awk WHATEVER.sql | sqlplus -s USER/PASSWORD@BLABLA
#
# Thomas Knudsen, SDFE - the Danish National Mapping Agency,  thokn@sdfe.dk
# 2018-12-05
# --------------------------------------------------------------------------------

$1=="Insert" && $2=="into" {
    print
    getline
    sub(/\(OBJECTID, /, "(")
}

$1=="Values" {
    print
    getline
    sub(/\([[:space:]]*[+-]?[0-9]+, /, "(")
}

{print}
