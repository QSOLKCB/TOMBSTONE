static const char fixed[5] = "null";
static char writable[5];
/*@ assigns \nothing;
    ensures const_readable: \valid_read(fixed+(0..4));
    ensures const_not_writable: !\valid((char *)fixed+(0..4));
    ensures ordinary_writable: \valid(writable+(0..4));
*/
int readonly_model_probe(void) {
    const char *p = "kind";
    /*@ assert literal_readable: \valid_read(p+(0..4)); */
    /*@ assert literal_not_writable: !\valid((char *)p+(0..4)); */
    return 1;
}
