# Checked reference trail

Original sources accessed on 6 November 2026. Source discovery and passage checking were AI-assisted; the author should read the linked passages before submission.

[1] K. Moriarty, B. Kaliski, and A. Rusch, PKCS #5: Password-Based Cryptography Specification Version 2.1, RFC 8018, Jan. 2017, sec. 5.2.

https://www.rfc-editor.org/rfc/rfc8018.html

Claim and source type: Informational RFC; PBKDF2 inputs and iterative construction.

[2] Python Software Foundation, CPython v3.14.7, Modules/_hashopenssl.c, pbkdf2_hmac_impl, lines 1296-1301, 2026.

https://github.com/python/cpython/blob/v3.14.7/Modules/_hashopenssl.c#L1296-L1301

Claim and source type: Version-pinned source; OpenSSL call inside allow-threads region.

[3] Python Software Foundation, Thread states and the global interpreter lock, Python 3.14 C API documentation.

https://docs.python.org/3.14/c-api/threads.html

Claim and source type: Technical documentation; GIL and detaching thread state. Rolling 3.14 documentation, not version-pinned 3.14.7.

[4] Python Software Foundation, concurrent.futures - Launching parallel tasks, Python 3.14 documentation.

https://docs.python.org/3.14/library/concurrent.futures.html

Claim and source type: Technical documentation; executor map and context-managed shutdown.

[5] Intel Corporation, Intel Core i5-12500H Processor Specifications.

https://www.intel.com/content/www/us/en/products/sku/96141/intel-core-i512500h-processor-18m-cache-up-to-4-50-ghz/specifications.html

Claim and source type: Vendor specifications; 4 P-cores, 8 E-cores, 16 threads. Not a measurement of our worker placement.

[6] T. Kalibera and R. Jones, Rigorous Benchmarking in Reasonable Time, Proc. ISMM, pp. 63-74, 2013, doi:10.1145/2464157.2464160.

https://kar.kent.ac.uk/33611/

Claim and source type: Peer-reviewed methodology; author manuscript read at https://kar.kent.ac.uk/33611/45/p63-kaliber.pdf. Repetition and uncertainty. Our study does not implement its full statistical method.

[7] A. Georges, D. Buytaert, and L. Eeckhout, Statistically Rigorous Java Performance Evaluation, Proc. OOPSLA, pp. 57-76, 2007, doi:10.1145/1297027.1297033.

https://dri.es/files/oopsla07-georges.pdf

Claim and source type: Peer-reviewed Java study; startup versus steady-state and variability. Used as methodological background, not direct evidence about CPython.